import asyncio
import logging
import json
from typing import Any, Dict, List, Set, Tuple

from langchain_core.prompts import PromptTemplate
from loguru import logger

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.ai.query_decomposer import decompose_query
from open_notebook.domain.notebook import vector_search
from open_notebook.ai.validator import OutputSchemaValidator
from open_notebook.ai.confidence_estimator import estimate_report_confidence
import os

# Limits and Configs
MAX_PARALLEL_SUBQUERIES = 5
SUBQUERY_TIMEOUT_SEC = 12.0
ORCHESTRATOR_TIMEOUT_SEC = 60.0
TOP_K_CHUNKS = 6

SUBQUERY_EXECUTION_PROMPT = """You are a focused research assistant.
Answer the following specific sub-question based ONLY on the provided context.
Do not invent facts. Do not include information outside the scope of the context.
If the context does not contain enough information to answer the question, state: "Insufficient information provided."

CONTEXT:
{context}

QUESTION:
{question}
"""

SYNTHESIS_PROMPT = """You are an expert synthesizer.
Given a sequence of targeted sub-answers, construct a comprehensive JSON Research Report that addresses the original user query.

CRITICAL INSTRUCTIONS:
1. Use ONLY the information from the provided subquery answers.
2. Do not invent additional claims or facts outside the provided answers.
3. If the sub-answers conflict, report the conflict instead of guessing.
4. Return ONLY valid JSON matching the system's generated report structure. Do not include markdown blocks or explanations.

ORIGINAL USER QUERY:
{original_query}

SUBQUERY FINDINGS:
{subquery_results}
"""

async def execute_subquery(subquery: Dict[str, Any], semaphore: asyncio.Semaphore) -> Dict[str, Any]:
    """
    Executes a single subquery with a concurrency limit and timeout.
    Retrieves vector chunks and prompts an LLM for an answer.
    """
    async with semaphore:
        try:
            return await asyncio.wait_for(_execute_subquery_internal(subquery), timeout=SUBQUERY_TIMEOUT_SEC)
        except asyncio.TimeoutError:
            logger.warning(f"Subquery timeout exceeded ({SUBQUERY_TIMEOUT_SEC}s) for subquery: '{subquery['text']}'")
            return {
                "subquery": subquery["text"],
                "answer": "Error: Timeout exceeded while researching this specific subquestion.",
                "sources": []
            }
        except Exception as e:
            logger.error(f"Error executing subquery '{subquery['text']}': {e}")
            return {
                "subquery": subquery["text"],
                "answer": f"Error: Failed to execute subquestion due to internal error.",
                "sources": []
            }

async def _execute_subquery_internal(subquery: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Bounded Retrieval
    results = await vector_search(subquery["text"], limit=TOP_K_CHUNKS)
    
    if not results:
        return {"subquery": subquery["text"], "answer": "Insufficient information provided.", "sources": []}
    
    # 2. Format Context
    context_blocks = []
    source_uris = []
    
    for r in results:
        # Avoid huge context windows dynamically, keeping it bounded conceptually
        block = f"[Source: {r.get('id', 'unknown')}]\n{r.get('text', '')}"
        context_blocks.append(block)
        
        # Propagating sources (from chunk parent link if available)
        parent_source = r.get("source")
        if parent_source:
             # Just keeping the ID reference for origin tracing
            if isinstance(parent_source, str):
                source_uris.append(parent_source)
            elif isinstance(parent_source, dict) and "id" in parent_source:
                source_uris.append(parent_source["id"])

    context_str = "\n\n".join(context_blocks)
    
    # 3. LLM Answer Generation
    prompt = PromptTemplate.from_template(SUBQUERY_EXECUTION_PROMPT)
    llm = await provision_langchain_model(context_str, None, "tools", temperature=0) # Deterministic
    chain = prompt | llm

    ai_message = await chain.ainvoke({"context": context_str, "question": subquery["text"]})
    answer = ai_message.content
    
    return {
        "subquery": subquery["text"],
        "answer": answer,
        "sources": list(set(source_uris)) # Unique sources for this subquery
    }

async def synthesize_report(original_query: str, subquery_results: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], List[str]]:
    """Takes all completed subquery results and aggregates them into a final JSON report."""
    
    # Format the input for the synthesis prompt
    formatted_results = "\n\n".join([
        f"Subquestion: {r['subquery']}\nAnswer: {r['answer']}" 
        for r in subquery_results
    ])
    
    # Aggregate all sources via Set Union
    all_sources = set()
    for r in subquery_results:
        all_sources.update(r["sources"])
        
    prompt = PromptTemplate.from_template(SYNTHESIS_PROMPT)
    llm = await provision_langchain_model(formatted_results, None, "tools", temperature=0, structured=dict(type="json"))
    chain = prompt | llm
    
    ai_message = await chain.ainvoke({
        "original_query": original_query, 
        "subquery_results": formatted_results
    })
    
    raw_json_str = ai_message.content
    
    # Validation against Schema
    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "schemas", "research_report.schema.json"
    )
    validator = OutputSchemaValidator(schema_path)
    valid_json_dict = await validator.validate_and_fix(raw_json_str, max_retries=2, timeout_sec=8.0)
    
    return valid_json_dict, list(all_sources)

async def run_orchestrated_research(query: str) -> Dict[str, Any]:
    """
    Main entrypoint for the background Orchestrator.
    Decomposes, executes in parallel, synthesizes, and returns the structured report JSON.
    Wrapped in a global orchestration timeout.
    """
    try:
        return await asyncio.wait_for(_run_orchestrated_research_internal(query), timeout=ORCHESTRATOR_TIMEOUT_SEC)
    except asyncio.TimeoutError:
         logger.error(f"Global orchestration timeout exceeded ({ORCHESTRATOR_TIMEOUT_SEC}s) for query: {query}")
         raise TimeoutError("Research orchestration took too long and was aborted.")

async def _run_orchestrated_research_internal(query: str) -> Dict[str, Any]:
    # 1. Decomposition (handles Deduplication and Heuristics internally)
    subqueries = await decompose_query(query)
    
    logger.info(f"Orchestrator branching into {len(subqueries)} parallel subqueries.")
    
    # 2. Parallel Execution with Semaphore Guard
    semaphore = asyncio.Semaphore(MAX_PARALLEL_SUBQUERIES)
    tasks = [execute_subquery(sq, semaphore) for sq in subqueries]
    
    subquery_results = await asyncio.gather(*tasks)
    
    # 3. Synthesis & Provenance Union
    structured_content, union_sources = await synthesize_report(query, subquery_results)
    
    # 4. Final Confidence Injection
    confidence_score = estimate_report_confidence(structured_content)
    structured_content["confidence"] = confidence_score
    
    # Inject aggregated sources into the metadata
    if "metadata" not in structured_content:
        structured_content["metadata"] = {}
    structured_content["metadata"]["orchestrator_subqueries_executed"] = len(subqueries)
    structured_content["metadata"]["aggregated_sources"] = union_sources
    
    return structured_content

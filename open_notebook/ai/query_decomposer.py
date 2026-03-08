import asyncio
import logging
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.utils.embedding import generate_embeddings
import numpy as np

logger = logging.getLogger(__name__)

# Heuristic lists
COMPARISON_KEYWORDS = {
    "compare", "difference", "vs", "versus", "impact", "relationship", "between"
}

class Subquery(BaseModel):
    id: str = Field(..., description="Unique identifier for the subquery, e.g., 'sq_1'.")
    text: str = Field(..., description="The specific question or instruction for this subquery.")
    intent: Literal["fact", "comparison", "definition", "timeline", "cause_effect"] = Field(
        ..., description="The classified primary intent of the subquery."
    )
    priority: int = Field(..., description="Execution priority (lower number = higher priority, e.g., 1 is highest).")
    schema_section: str = Field(..., description="The generic topic area or schema property this focuses on.")

class QueryDecompositionResult(BaseModel):
    subqueries: List[Subquery] = Field(description="List of decomposed subqueries, max 5.")

DECOMPOSITION_PROMPT = """You are an expert query orchestrator.
Your task is to decompose a complex user query into a sequence of simpler, focused subqueries that can be executed in parallel or sequentially.

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON matching the schema.
2. Do not include any explanations, reasoning, or thought processes.
3. Do not include markdown formatting like ```json blocks.
4. Generate a MAXIMUM of 5 subqueries.
5. Each subquery must target a distinct aspect of the original question.
6. Assign priority (1 is highest, execute first). Base facts should have priority 1, comparisons priority 2, etc.

USER QUERY:
{query}
"""

async def _deduplicate_subqueries(subqueries: List[Dict[str, Any]], threshold: float = 0.9) -> List[Dict[str, Any]]:
    """Deduplicate subqueries based on semantic similarity."""
    if len(subqueries) <= 1:
        return subqueries

    texts = [sq["text"] for sq in subqueries]
    try:
        embeddings = await generate_embeddings(texts)
    except Exception as e:
        logger.warning(f"Failed to generate embeddings for deduplication: {e}. Skipping deduplication.")
        return subqueries
        
    arr = np.array(embeddings, dtype=np.float64)
    # Normalize
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms = np.where(norms > 0, norms, 1.0)
    arr = arr / norms
    
    # Compute similarity matrix
    sim_matrix = np.dot(arr, arr.T)
    
    unique_indices = []
    for i in range(len(subqueries)):
        is_duplicate = False
        for j in unique_indices:
            if sim_matrix[i, j] > threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_indices.append(i)
            
    return [subqueries[i] for i in unique_indices]

def should_bypass_decomposition(query: str) -> bool:
    """Returns True if the query should bypass the LLM and be executed directly."""
    words = query.lower().split()
    if len(words) <= 2:
        # Check if words intersect with comparison keywords
        if not any(word in COMPARISON_KEYWORDS for word in words):
            return True
    return False

async def decompose_query(query: str) -> List[Dict[str, Any]]:
    """
    Decomposes a complex query into subqueries.
    Applies heuristics, LLM structured output, deduplication, and a 2-second timeout.
    """
    query = query.strip()
    if not query:
        return []

    # 1. Fallback Rule Heuristic
    if should_bypass_decomposition(query):
        logger.info("Query decomposition bypassed (heuristic match).")
        return [{
            "id": "sq_1",
            "text": query,
            "intent": "fact",
            "priority": 1,
            "schema_section": "general"
        }]

    # 2. LLM Invocation with Timeout Guard
    try:
        prompt = PromptTemplate.from_template(DECOMPOSITION_PROMPT)
        llm = await provision_langchain_model(query, None, "tools", temperature=0)
        chain = prompt | llm.with_structured_output(QueryDecompositionResult)

        # 2-second timeout guard
        result = await asyncio.wait_for(chain.ainvoke({"query": query}), timeout=2.0)
        
        # Parse result
        raw_subqueries = [sq.model_dump() for sq in result.subqueries[:5]]
        
        # 3. Deduplication
        unique_subqueries = await _deduplicate_subqueries(raw_subqueries)
        
        logger.info(f"Decomposition complete: generated {len(unique_subqueries)} subqueries.")
        return unique_subqueries

    except asyncio.TimeoutError:
        logger.warning("Query decomposition timed out (>2s). Falling back to single query.")
        return [{
            "id": "sq_1",
            "text": query,
            "intent": "fact",
            "priority": 1,
            "schema_section": "general"
        }]
    except Exception as e:
        logger.error(f"Failed to decompose query: {e}. Falling back to single query.")
        return [{
            "id": "sq_1",
            "text": query,
            "intent": "fact",
            "priority": 1,
            "schema_section": "general"
        }]

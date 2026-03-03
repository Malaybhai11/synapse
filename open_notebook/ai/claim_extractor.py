import json
import logging
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate

from open_notebook.ai.provision import provision_langchain_model

logger = logging.getLogger(__name__)

# Pydantic definition matching the core of claim.schema.json
class ExtractedClaim(BaseModel):
    text: str = Field(..., description="The textual content of the claim, max 1000 chars.")
    subject: str = Field(..., description="The subject of the claim.")
    predicate: str = Field(..., description="The action or property attributed to the subject.")
    object: str = Field(..., description="The entity or value receiving the action or completing the property.")
    polarity: Literal["supports", "opposes", "neutral"] = Field(..., description="The stance of this claim relative to the research topic. Must be 'supports', 'opposes', or 'neutral'.")
    confidence: float = Field(..., description="Confidence score for the claim (0-1).", ge=0.0, le=1.0)
    source_id: str = Field(
        default="unknown", 
        description="ID of the source document supporting this claim if explicitly mentioned, else 'unknown'."
    )

class ClaimExtractionResult(BaseModel):
    claims: List[ExtractedClaim] = Field(description="List of extracted atomic claims, max 5 per section.")

CLAIM_EXTRACTION_PROMPT = """You are an expert epistemological analyst.
Your task is to extract atomic, verifiable claims from the provided analytical text.

CRITICAL RULES:
1. Each claim MUST represent a single factual proposition with ONE subject-predicate-object triple. No conjunctions. No compound statements.
2. Extract a MAXIMUM of 5 claims from the provided text.
3. Only extract the most structurally significant and objectively verifiable claims.
4. If there are fewer than 5 valid claims, only extract what is valid. Do not force 5.

TEXT TO ANALYZE:
{text}
"""

async def extract_claims_from_text(text: str, max_claims: int = 5) -> List[Dict[str, Any]]:
    """
    Uses an LLM with structured output to extract atomic claims from a block of text.
    Strictly enforces a max_claims cap.
    """
    if not text.strip():
        return []

    prompt = PromptTemplate.from_template(CLAIM_EXTRACTION_PROMPT)
    llm = await provision_langchain_model(text, None, "tools", temperature=0) # Deterministic model

    chain = prompt | llm.with_structured_output(ClaimExtractionResult)

    try:
        result = await chain.ainvoke({"text": text})
        # Hard scale-cap logic to prevent graph explosion
        claims = result.claims[:max_claims]
        return [claim.model_dump() for claim in claims]
    except Exception as e:
        logger.error(f"Failed to extract claims: {e}")
        return []

async def process_report_for_claims(report_content: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Takes a GeneratedReport structured_content (JSON), safely slices out 
    the analytical sections (ignoring metadata and sources to prevent pollution), 
    and extracts atomic claims in batches.
    """
    all_claims = []

    # 1. Executive Summary
    exec_summary = report_content.get("executive_summary", "")
    if isinstance(exec_summary, str) and exec_summary:
        claims = await extract_claims_from_text(f"[EXECUTIVE SUMMARY]\n{exec_summary}")
        all_claims.extend(claims)

    # 2. Technical Breakdown (Iterates per section)
    tech_breakdown = report_content.get("technical_breakdown", [])
    if isinstance(tech_breakdown, list):
        for section in tech_breakdown:
            topic = section.get("topic", "")
            text = section.get("text", "")
            evidence = section.get("evidence", "")
            # Merge text and evidence for better source_id pulling
            block = text
            if evidence:
                block += f"\n[EVIDENCE: {evidence}]"
            
            if block:
                claims = await extract_claims_from_text(f"[TECHNICAL BREAKDOWN - {topic}]\n{block}")
                all_claims.extend(claims)

    # 3. Pros and Cons
    pros = report_content.get("pros", [])
    cons = report_content.get("cons", [])
    if pros or cons:
        text_block = ""
        if pros:
            text_block += "[PROS]\n" + "\n".join(pros) + "\n"
        if cons:
            text_block += "[CONS]\n" + "\n".join(cons) + "\n"
        if text_block:
            claims = await extract_claims_from_text(text_block)
            all_claims.extend(claims)

    # 4. Comparison Table
    comp_table = report_content.get("comparison_table", {})
    if comp_table:
        # Flatten the table structure into a readable text block for LangChain
        rows = comp_table.get("rows", [])
        if rows:
            table_text = "[COMPARISON TABLE]\n" + json.dumps(rows, indent=2)
            claims = await extract_claims_from_text(table_text)
            all_claims.extend(claims)

    return all_claims

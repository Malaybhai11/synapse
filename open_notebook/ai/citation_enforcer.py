import logging
from typing import Any, Dict, List, Tuple
from datetime import datetime, timezone

from open_notebook.database.repository import repo_query, ensure_record_id
from open_notebook.domain.notebook import Claim, GeneratedReport
from open_notebook.utils.embedding import generate_embedding

logger = logging.getLogger(__name__)

GROUNDING_THRESHOLD = 0.55

async def calculate_grounding_score(avg_similarity: float, retrieval_score: float, num_chunks: int) -> float:
    """
    Computes a weighted grounding score.
    Formula: (avg_sim * 0.6) + (retrieval_score * 0.25) + (min(num_chunks / 3, 1.0) * 0.15)
    """
    chunk_bonus = min(num_chunks / 3.0, 1.0) * 0.15
    score = (avg_similarity * 0.6) + (retrieval_score * 0.25) + chunk_bonus
    return score

def get_grounding_strength(score: float) -> str:
    """Soft tiering for grounding strength."""
    if score > 0.75:
        return "strongly grounded"
    elif score >= GROUNDING_THRESHOLD:
        return "weakly grounded"
    else:
        return "ungrounded"

async def cosine_similarity_multi(v1: List[float], vectors: List[List[float]]) -> List[float]:
    """Computes cosine similarity between a vector and a list of vectors."""
    import numpy as np
    if not vectors:
        return []
    
    a = np.array(v1)
    b = np.array(vectors)
    
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b, axis=1)
    
    # Avoid division by zero
    norm_b = np.where(norm_b == 0, 1e-10, norm_b)
    
    dot_product = np.dot(b, a)
    similarities = dot_product / (norm_a * norm_b)
    return similarities.tolist()

async def find_supporting_chunks(claim_text: str, report_id: str, top_k: int = 3) -> Tuple[List[Dict[str, Any]], float]:
    """
    Two-step search for supporting chunks:
    1. Search chunks linked to the report's sources first.
    2. Fallback to global search if necessary (or if threshold not met).
    """
    report_id_record = ensure_record_id(report_id)
    
    # Get report's source IDs first
    report = await GeneratedReport.get(str(report_id))
    source_ids = []
    if report and report.structured_content:
        # Extract source IDs from structured content if possible
        sources = report.structured_content.get("sources", [])
        source_ids = [ensure_record_id(s.get("doc_id")) for s in sources if s.get("doc_id")]

    claim_embedding = await generate_embedding(claim_text)
    
    # Step 1: Search within report sources
    supporting_chunks = []
    max_sim = 0.0
    
    if source_ids:
        # Query for chunks linked to these sources
        # We'll use a vector search limited to these sources if possible
        # For now, let's fetch chunks for these sources and compute similarity manually or via a targeted query
        chunks = await repo_query(
            "SELECT id, content, embedding, source FROM source_embedding WHERE source INSIDE $source_ids",
            {"source_ids": source_ids}
        )
        
        if chunks:
            chunk_embeddings = [c["embedding"] for c in chunks if c.get("embedding")]
            if chunk_embeddings:
                similarities = await cosine_similarity_multi(claim_embedding, chunk_embeddings)
                for i, sim in enumerate(similarities):
                    chunks[i]["similarity"] = sim
                
                # Sort and take top_k
                chunks.sort(key=lambda x: x.get("similarity", 0), reverse=True)
                supporting_chunks = chunks[:top_k]
                max_sim = supporting_chunks[0]["similarity"] if supporting_chunks else 0.0

    # Step 2: Global fallback if threshold not met
    if max_sim < GROUNDING_THRESHOLD:
        logger.debug(f"Local grounding failed ({max_sim:.2f}), attempting global fallback for claim: {claim_text[:50]}...")
        # Use vector_search function for global search
        from open_notebook.domain.notebook import vector_search
        global_results = await vector_search(claim_text, results=top_k, source=False, note=False, minimum_score=GROUNDING_THRESHOLD)
        
        if global_results:
            # global_results from vector_search usually return simplified objects
            # We need to adapt them to our chunk structure
            for res in global_results:
                # Assuming vector_search returns matching source_embedding records or similar
                # If it's a dedicated function, it might return a specific format
                supporting_chunks.append({
                    "id": res["id"],
                    "content": res.get("content", ""),
                    "similarity": res.get("score", 0.0),
                    "source": res.get("source")
                })
            
            # Re-sort and re-cap
            supporting_chunks.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            supporting_chunks = supporting_chunks[:top_k]

    # Calculate average retrieval score (using similarity as a proxy)
    avg_retrieval_score = sum(c.get("similarity", 0.0) for c in supporting_chunks) / len(supporting_chunks) if supporting_chunks else 0.0
    
    return supporting_chunks, avg_retrieval_score

async def enforce_citation(claim: Claim, report_id: str) -> Claim:
    """Enforces citation for a single claim."""
    chunks, avg_retrieval_score = await find_supporting_chunks(claim.text, report_id)
    
    num_chunks = len(chunks)
    avg_sim = avg_retrieval_score # Simplification for now
    
    grounding_score = await calculate_grounding_score(avg_sim, avg_retrieval_score, num_chunks)
    
    claim.evidence_chunks = [str(c["id"]) for c in chunks]
    claim.source_documents = list(set([str(c["source"]) for c in chunks if c.get("source")]))
    claim.evidence_score = grounding_score
    claim.grounding_strength = get_grounding_strength(grounding_score)
    claim.grounded = grounding_score >= GROUNDING_THRESHOLD
    claim.grounding_method = "vector_similarity_v1"
    claim.grounded_at = datetime.now(timezone.utc)
    
    return claim

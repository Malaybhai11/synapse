import pytest
import asyncio
from unittest.mock import MagicMock, patch
from open_notebook.ai.citation_enforcer import calculate_grounding_score, get_grounding_strength, enforce_citation
from open_notebook.domain.notebook import Claim

@pytest.mark.asyncio
async def test_calculate_grounding_score():
    # Test high similarity, high retrieval, high redundancy
    score = await calculate_grounding_score(avg_similarity=0.9, retrieval_score=0.9, num_chunks=3)
    # (0.9 * 0.6) + (0.9 * 0.25) + (1.0 * 0.15) = 0.54 + 0.225 + 0.15 = 0.915
    assert score == pytest.approx(0.915)
    
    # Test low similarity
    score = await calculate_grounding_score(avg_similarity=0.4, retrieval_score=0.4, num_chunks=1)
    # (0.4 * 0.6) + (0.4 * 0.25) + (0.333 * 0.15) = 0.24 + 0.10 + 0.05 = 0.39
    assert score < 0.55

def test_get_grounding_strength():
    assert get_grounding_strength(0.8) == "strongly grounded"
    assert get_grounding_strength(0.6) == "weakly grounded"
    assert get_grounding_strength(0.4) == "ungrounded"

@pytest.mark.asyncio
async def test_hallucination_detection():
    # Mocking find_supporting_chunks to return no evidence for a hallucinated claim
    with patch("open_notebook.ai.citation_enforcer.find_supporting_chunks") as mock_find:
        mock_find.return_value = ([], 0.0) # No chunks found
        
        claim = Claim(
            text="Synapse was developed by NASA in 1998",
            subject="Synapse",
            predicate="developed by",
            object="NASA",
            polarity="supports",
            confidence=0.9,
            source_id="source:1",
            report_id="report:1"
        )
        
        with patch("open_notebook.ai.citation_enforcer.generate_embedding", return_value=[0.1]*1536):
            updated_claim = await enforce_citation(claim, "report:1")
            
            assert updated_claim.grounded is False
            assert updated_claim.grounding_strength == "ungrounded"
            assert updated_claim.evidence_score < 0.55
            assert len(updated_claim.evidence_chunks) == 0

@pytest.mark.asyncio
async def test_global_fallback():
    # Mocking find_supporting_chunks to return evidence from global search
    with patch("open_notebook.ai.citation_enforcer.find_supporting_chunks") as mock_find:
        # Mocking a successful global find
        mock_find.return_value = ([
            {"id": "chunk:global_1", "source": "source:external", "similarity": 0.8}
        ], 0.8)
        
        claim = Claim(
            text="Transformer models outperform RNNs",
            subject="Transformer models",
            predicate="outperform",
            object="RNNs",
            polarity="supports",
            confidence=0.9,
            source_id="source:1",
            report_id="report:1"
        )
        
        with patch("open_notebook.ai.citation_enforcer.generate_embedding", return_value=[0.1]*1536):
            updated_claim = await enforce_citation(claim, "report:1")
            
            assert updated_claim.grounded is True
            assert "chunk:global_1" in updated_claim.evidence_chunks
            assert "source:external" in updated_claim.source_documents

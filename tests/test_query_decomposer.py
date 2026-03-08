import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from open_notebook.ai.query_decomposer import (
    should_bypass_decomposition,
    decompose_query,
    _deduplicate_subqueries,
    Subquery
)

def test_heuristic_bypass():
    # Should bypass: 1 or 2 words, no comparison keywords
    assert should_bypass_decomposition("Apple") is True
    assert should_bypass_decomposition("Steve Jobs") is True

    # Should NOT bypass: comparison keywords even if short
    assert should_bypass_decomposition("Apple vs") is False
    assert should_bypass_decomposition("compare Apple") is False

    # Should NOT bypass: more than 2 words
    assert should_bypass_decomposition("Who is Steve Jobs") is False
    assert should_bypass_decomposition("Apple Microsoft Google") is False

@pytest.mark.asyncio
async def test_deduplication():
    # Helper to create mock subqueries
    sq1 = {"id": "1", "text": "What is the revenue of Apple in Q3?"}
    sq2 = {"id": "2", "text": "How much revenue did Apple generate in Q3?"} # Similar to sq1
    sq3 = {"id": "3", "text": "Who is the CEO of Microsoft?"}
    
    # Mock generate_embeddings to return similar vectors for 1 and 2, different for 3
    with patch("open_notebook.ai.query_decomposer.generate_embeddings") as mock_emb:
        # These are fake normalized vectors
        mock_emb.return_value = [
            [1.0, 0.0, 0.0],  # sq1
            [0.98, 0.1, 0.0], # sq2 (highly similar to sq1)
            [0.0, 1.0, 0.0]   # sq3 (orthogonal)
        ]
        
        result = await _deduplicate_subqueries([sq1, sq2, sq3], threshold=0.9)
        # Should keep sq1 and sq3, dropping sq2
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "3"

@pytest.mark.asyncio
async def test_timeout_fallback():
    query = "Compare Apple and Microsoft revenue over 5 years"
    
    # Mock LLM to sleep for 3 seconds, triggering the 2-second timeout
    async def mock_ainvoke(*args, **kwargs):
        await asyncio.sleep(3.0)
        return MagicMock()

    mock_chain = AsyncMock()
    mock_chain.ainvoke.side_effect = mock_ainvoke
    
    with patch("open_notebook.ai.query_decomposer.PromptTemplate.from_template") as mock_prompt_from_template, \
         patch("open_notebook.ai.query_decomposer.provision_langchain_model", new_callable=AsyncMock) as mock_provision:
        
        mock_prompt = MagicMock()
        mock_prompt.__or__.return_value = mock_chain
        mock_prompt_from_template.return_value = mock_prompt
        
        mock_llm = MagicMock()
        mock_provision.return_value = mock_llm
        
        # This will hit the timeout and fallback
        result = await decompose_query(query)
        
        # Verify fallback behavior
        assert len(result) == 1
        assert result[0]["text"] == query
        assert result[0]["id"] == "sq_1"
        assert result[0]["intent"] == "fact"

@pytest.mark.asyncio
async def test_successful_decomposition():
    query = "Compare Apple and Microsoft"
    
    # Mock successful LLM response
    mock_subq1 = Subquery(id="sq_1", text="What is Apple's revenue?", intent="fact", priority=1, schema_section="financials")
    mock_subq2 = Subquery(id="sq_2", text="What is Microsoft's revenue?", intent="fact", priority=1, schema_section="financials")
    mock_result = MagicMock()
    mock_result.subqueries = [mock_subq1, mock_subq2]
    
    mock_chain = AsyncMock()
    mock_chain.ainvoke.return_value = mock_result
    
    with patch("open_notebook.ai.query_decomposer.PromptTemplate.from_template") as mock_prompt_from_template, \
         patch("open_notebook.ai.query_decomposer.provision_langchain_model", new_callable=AsyncMock) as mock_provision, \
         patch("open_notebook.ai.query_decomposer._deduplicate_subqueries", new_callable=AsyncMock) as mock_dedup:
             
        mock_prompt = MagicMock()
        mock_prompt.__or__.return_value = mock_chain
        mock_prompt_from_template.return_value = mock_prompt
             
        mock_llm = MagicMock()
        mock_provision.return_value = mock_llm
        
        # Mock dedup just returning the input
        mock_dedup.return_value = [sq.model_dump() for sq in mock_result.subqueries]
        
        result = await decompose_query(query)
        
        assert len(result) == 2
        assert result[0]["text"] == "What is Apple's revenue?"
        assert result[1]["text"] == "What is Microsoft's revenue?"

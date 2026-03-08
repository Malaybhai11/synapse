import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

from open_notebook.ai.research_orchestrator import run_orchestrated_research, execute_subquery

@pytest.fixture
def mock_subqueries():
    return [
        {"id": "sq_1", "text": "Feature A details", "intent": "fact", "priority": 1, "schema_section": "general"},
        {"id": "sq_2", "text": "Feature B details", "intent": "fact", "priority": 1, "schema_section": "general"}
    ]

@pytest.fixture
def mock_vector_results():
    return [
        {"id": "doc_1", "text": "Chunk about A", "source": "uri_1"},
        {"id": "doc_2", "text": "Chunk about B", "source": {"id": "uri_2"}}
    ]

@pytest.mark.asyncio
async def test_orchestrator_end_to_end(mock_subqueries, mock_vector_results):
    """
    Tests the happy path: decomposition -> parallel execution -> aggregation.
    """
    with patch("open_notebook.ai.research_orchestrator.decompose_query", new_callable=AsyncMock) as mock_decompose, \
         patch("open_notebook.ai.research_orchestrator.vector_search", new_callable=AsyncMock) as mock_search, \
         patch("open_notebook.ai.research_orchestrator.provision_langchain_model", new_callable=AsyncMock) as mock_provision, \
         patch("open_notebook.ai.research_orchestrator.PromptTemplate.from_template") as mock_prompt_from_template, \
         patch("open_notebook.ai.research_orchestrator.OutputSchemaValidator.validate_and_fix", new_callable=AsyncMock) as mock_validate, \
         patch("open_notebook.ai.research_orchestrator.estimate_report_confidence") as mock_confidence:
        
        mock_decompose.return_value = mock_subqueries
        mock_search.return_value = mock_vector_results
        
        # Setup LLM chain mock to return fixed string
        mock_ai_message = MagicMock()
        mock_ai_message.content = "LLM Response"
        
        mock_chain = AsyncMock()
        mock_chain.ainvoke.return_value = mock_ai_message
        
        mock_prompt = MagicMock()
        mock_prompt.__or__.return_value = mock_chain
        mock_prompt_from_template.return_value = mock_prompt
        
        # Setup Validator return
        mock_validate.return_value = {"title": "Integrated Report", "sections": []}
        mock_confidence.return_value = 0.95
        
        result = await run_orchestrated_research("Compare A and B")
        
        # Verify gathers executed correctly
        assert mock_search.call_count == 2
        # Number of ainokes = 2 subqueries + 1 synthesis
        assert mock_chain.ainvoke.call_count == 3
        
        # Verify metadata injection
        assert result["confidence"] == 0.95
        assert result["metadata"]["orchestrator_subqueries_executed"] == 2
        
        # Verify provenance union (source_uris)
        sources = result["metadata"]["aggregated_sources"]
        assert "uri_1" in sources
        assert "uri_2" in sources


@pytest.mark.asyncio
async def test_subquery_failure_recovery(mock_subqueries):
    """
    Tests if the orchestrator survives when one subquery raises an Exception.
    """
    with patch("open_notebook.ai.research_orchestrator.decompose_query", new_callable=AsyncMock) as mock_decompose, \
         patch("open_notebook.ai.research_orchestrator.vector_search", new_callable=AsyncMock) as mock_search, \
         patch("open_notebook.ai.research_orchestrator.synthesize_report", new_callable=AsyncMock) as mock_synthesize, \
         patch("open_notebook.ai.research_orchestrator.estimate_report_confidence") as mock_conf:
         
        mock_decompose.return_value = mock_subqueries
        
        # Make vector_search fail specifically for the second subquery
        async def side_effect_search(query, *args, **kwargs):
            if "B" in query:
                raise ValueError("Simulated Database Error")
            return [{"id": "doc_1", "text": "Success Chunk", "source": "uri_1"}]
            
        mock_search.side_effect = side_effect_search
        
        # Mock LLM generation for the successful one to bypass provision logic
        with patch("open_notebook.ai.research_orchestrator._execute_subquery_internal", new_callable=AsyncMock) as mock_internal:
            
            # Use original for A, wrap exception manually for B as side_effect setup
            pass # Actually an easier way is to patch vector_search, let's keep it.
            
            # Since we patched _execute_subquery_internal, we need to mock vector_search INSIDE the internal call.
            # But wait, execute_subquery is what catches exceptions.
            
    with patch("open_notebook.ai.research_orchestrator.decompose_query", new_callable=AsyncMock) as mock_decompose, \
         patch("open_notebook.ai.research_orchestrator._execute_subquery_internal", new_callable=AsyncMock) as mock_internal_exec, \
         patch("open_notebook.ai.research_orchestrator.synthesize_report", new_callable=AsyncMock) as mock_synthesize, \
         patch("open_notebook.ai.research_orchestrator.estimate_report_confidence") as mock_conf:
        
        mock_decompose.return_value = mock_subqueries
        
        async def side_effect_exec(subquery):
            if subquery["id"] == "sq_2":
                raise ValueError("Failure in LLM or DB")
            return {"subquery": subquery["text"], "answer": "Success A", "sources": ["uri_1"]}
            
        mock_internal_exec.side_effect = side_effect_exec
        mock_synthesize.return_value = ({"title": "Report"}, ["uri_1"])
        mock_conf.return_value = 0.8
        
        # Action
        result = await run_orchestrated_research("Query A and B")
        
        # Verify it still succeeded using the remaining parts
        assert result["metadata"]["orchestrator_subqueries_executed"] == 2
        assert "uri_1" in result["metadata"]["aggregated_sources"]

@pytest.mark.asyncio
async def test_subquery_timeout(mock_subqueries):
    """
    Tests the 12 second per-subquery circuit breaker.
    """
    with patch("open_notebook.ai.research_orchestrator.decompose_query", new_callable=AsyncMock) as mock_decompose, \
         patch("open_notebook.ai.research_orchestrator._execute_subquery_internal", new_callable=AsyncMock) as mock_internal_exec, \
         patch("open_notebook.ai.research_orchestrator.synthesize_report", new_callable=AsyncMock) as mock_synthesize, \
         patch("open_notebook.ai.research_orchestrator.estimate_report_confidence") as mock_conf, \
         patch("open_notebook.ai.research_orchestrator.SUBQUERY_TIMEOUT_SEC", 0.1): # Low timeout for test
        
        mock_decompose.return_value = mock_subqueries
        
        async def side_effect_exec(subquery):
            if subquery["id"] == "sq_2":
                await asyncio.sleep(0.5) # Stall longer than timeout
                return {"subquery": subquery["text"], "answer": "Too Late", "sources": ["uri_stalled"]}
            return {"subquery": subquery["text"], "answer": "Fast Success", "sources": ["uri_fast"]}
            
        mock_internal_exec.side_effect = side_effect_exec
        mock_synthesize.return_value = ({"title": "Report"}, ["uri_fast"])
        mock_conf.return_value = 0.8
        
        # Action
        result = await run_orchestrated_research("Query A and B stall")
        
        # The Synthesis should receive one success and one timeout error string
        # We assert that the orchestrator itself doesn't crash on the TimeoutError
        assert result["metadata"]["orchestrator_subqueries_executed"] == 2
        # `uri_stalled` should definitely not be in the output provenance
        assert "uri_fast" in result["metadata"]["aggregated_sources"]

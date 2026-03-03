import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from open_notebook.ai.claim_extractor import extract_claims_from_text, process_report_for_claims, ExtractedClaim, ClaimExtractionResult
from commands.claim_commands import extract_claims_command, ExtractClaimsInput
from open_notebook.domain.notebook import GeneratedReport, Claim

@pytest.mark.asyncio
async def test_claim_extractor_caps():
    """Tests that the extractor strictly enforces the 5-claim scaling cap."""
    # Mock 10 LLM claims
    mock_claims = []
    for i in range(10):
        mock_claims.append(
            ExtractedClaim(
                text=f"Claim {i}",
                subject="Subject",
                predicate="Predicate",
                object="Object",
                polarity="neutral",
                confidence=0.9,
                source_id="unknown"
            )
        )
    mock_result = ClaimExtractionResult(claims=mock_claims)

    from langchain_core.runnables import RunnableLambda
    
    async def fake_ainvoke(x):
        return mock_result
        
    class FakeLLMWrapper:
        def with_structured_output(self, schema):
            return RunnableLambda(fake_ainvoke)

    with patch("open_notebook.ai.claim_extractor.provision_langchain_model", new_callable=AsyncMock) as mock_provision:
        mock_provision.return_value = FakeLLMWrapper()
        
        result = await extract_claims_from_text("Dummy analytical text")
        
        assert len(result) == 5  # The cap 
        assert result[0]["text"] == "Claim 0"
        assert result[4]["text"] == "Claim 4"

@pytest.mark.asyncio
async def test_process_report_for_claims_payload_filtering():
    """Tests that process_report_for_claims ONLY looks at analytics, skipping sources/metadata."""
    # Malformed / padded json with bad metadata
    mock_report = {
        "metadata": {"should_be_ignored": "Yes"},
        "sources": ["source 1", "source 2"],
        "executive_summary": "Exec text.",
        "technical_breakdown": [{"topic": "Topic A", "text": "Tech text"}]
    }
    
    with patch("open_notebook.ai.claim_extractor.extract_claims_from_text", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = [{"text": "Found claim"}]
        
        results = await process_report_for_claims(mock_report)
        
        # Should be called exactly twice: once for summary, once for tech breakdown
        assert mock_extract.call_count == 2
        # Verify it didn't pass metadata or sources
        call_args = [call[0][0] for call in mock_extract.call_args_list]
        assert "[EXECUTIVE SUMMARY]\nExec text." in call_args[0]
        assert "[TECHNICAL BREAKDOWN - Topic A]\nTech text" in call_args[1]

@pytest.mark.asyncio
async def test_extract_claims_command_idempotency():
    """Verify that if claims already run for report_id, the command gracefully skips processing."""
    mock_report = MagicMock()
    mock_report.claim_extraction_status = "complete"
    
    with patch("commands.claim_commands.GeneratedReport.get", new_callable=AsyncMock) as mock_get_report:
        mock_get_report.return_value = mock_report
        
        output = await extract_claims_command(ExtractClaimsInput(report_id="report:123"))
        
        assert output.success == True
        assert output.claims_extracted == 0
        mock_get_report.assert_called_once()

@pytest.mark.asyncio
async def test_extract_claims_command_batching():
    """Verify the command batches the vectors in one shot instead of executing an N+1 query loop."""
    with patch("commands.claim_commands.repo_query", new_callable=AsyncMock) as mock_repo_query:
        mock_repo_query.return_value = [] # No existing claims
        
        mock_report = MagicMock()
        mock_report.structured_content = {"executive_summary": "Dummy"}
        mock_report.claim_extraction_status = "pending"
        mock_report.save = AsyncMock()
        
        with patch("commands.claim_commands.GeneratedReport.get", new_callable=AsyncMock) as mock_get_report:
            mock_get_report.return_value = mock_report
            
            mock_extracted = [
                {"text": "Claim 1", "subject": "S", "predicate": "P", "object": "O", "polarity": "neutral", "confidence": 0.5, "source_id": "none"},
                {"text": "Claim 2", "subject": "S", "predicate": "P", "object": "O", "polarity": "neutral", "confidence": 0.5, "source_id": "none"}
            ]
            
            with patch("commands.claim_commands.process_report_for_claims", new_callable=AsyncMock) as mock_process:
                mock_process.return_value = mock_extracted
                
                with patch("commands.claim_commands.generate_embeddings", new_callable=AsyncMock) as mock_embed:
                    # Return parallel batched embeddings (Orthogonal to bypass cosine dedupe)
                    mock_embed.return_value = [[1.0, 0.0], [0.0, 1.0]]
                    
                    with patch("commands.claim_commands.Claim.save", new_callable=AsyncMock) as mock_save:
                    
                        output = await extract_claims_command(ExtractClaimsInput(report_id="report:123"))
                        
                        assert output.success == True
                        assert output.claims_extracted == 2
                        
                        # ASSERT IT WAS BATCHED IN ONE CALL
                        mock_embed.assert_called_once_with(["Claim 1", "Claim 2"]) 
                        assert mock_save.call_count == 2

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from commands.claim_commands import extract_claims_command, ExtractClaimsInput

@pytest.mark.asyncio
async def test_claim_extraction_concurrency():
    """Run 20 concurrent claim extractions to verify DB/async safety without contention."""
    
    # We will mock the DB get, save, process_report, generate_embeddings
    def create_mock_report(*args, **kwargs):
        mock_report = MagicMock()
        mock_report.structured_content = {"executive_summary": "Dummy summary"}
        mock_report.claim_extraction_status = "pending"
        mock_report.save = AsyncMock()
        return mock_report

    with patch("commands.claim_commands.GeneratedReport.get", new_callable=AsyncMock) as mock_get_report:
        mock_get_report.side_effect = create_mock_report
        
        with patch("commands.claim_commands.process_report_for_claims", new_callable=AsyncMock) as mock_process:
            mock_process.return_value = [
                {"text": "Atomic Claim 1", "subject": "S", "predicate": "P", "object": "O", "polarity": "neutral", "confidence": 0.5, "source_id": "none"},
                {"text": "Atomic Claim 2", "subject": "S", "predicate": "P", "object": "O", "polarity": "neutral", "confidence": 0.5, "source_id": "none"}
            ]
            
            with patch("commands.claim_commands.generate_embeddings", new_callable=AsyncMock) as mock_embed:
                # Fully orthogonal vectors so the deduplicator natively accepts both
                mock_embed.return_value = [[1.0, 0.0], [0.0, 1.0]] 
                
                with patch("commands.claim_commands.Claim.save", new_callable=AsyncMock) as mock_claim_save:
                    
                    # Spawn 20 simultaneous background tasks
                    tasks = [
                        extract_claims_command(ExtractClaimsInput(report_id=f"report:{i}"))
                        for i in range(20)
                    ]
                    
                    results = await asyncio.gather(*tasks)
                    
                    # Verify
                    assert len(results) == 20
                    for res in results:
                        assert res.success == True
                        
                    assert mock_get_report.call_count == 20
                    assert mock_process.call_count == 20
                    assert mock_embed.call_count == 20
                    assert mock_claim_save.call_count == 40  # 20 * 2 claims successfully bypassed guards

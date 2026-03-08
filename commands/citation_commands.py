import time
from typing import Optional, List
from loguru import logger
from surreal_commands import CommandInput, CommandOutput, command

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.notebook import Claim, GeneratedReport
from open_notebook.ai.citation_enforcer import enforce_citation

class EnforceCitationsInput(CommandInput):
    report_id: str

class EnforceCitationsOutput(CommandOutput):
    success: bool
    report_id: str
    claims_processed: int
    claims_grounded: int
    claims_ungrounded: int
    avg_grounding_score: float
    processing_time: float
    error_message: Optional[str] = None

@command(
    "enforce_citations",
    app="open_notebook",
    retry={
        "max_attempts": 2,
        "wait_strategy": "exponential_jitter",
        "wait_min": 2,
        "wait_max": 10,
        "retry_log_level": "debug",
    },
)
async def enforce_citations_command(input_data: EnforceCitationsInput) -> EnforceCitationsOutput:
    """
    Background job to enforce citation grounding for all claims extracted for a report.
    """
    start_time = time.time()
    try:
        report_id = ensure_record_id(input_data.report_id)
        
        # 1. Fetch all claims for this report
        claims_data = await repo_query(
            "SELECT * FROM claim WHERE report_id = $report_id",
            {"report_id": str(report_id)}
        )
        
        if not claims_data:
            logger.info(f"No claims found for report {report_id} to enforce citations.")
            return EnforceCitationsOutput(
                success=True,
                report_id=input_data.report_id,
                claims_processed=0,
                claims_grounded=0,
                claims_ungrounded=0,
                avg_grounding_score=0.0,
                processing_time=time.time() - start_time
            )

        claims = [Claim(**c) for c in claims_data]
        
        processed_count = 0
        grounded_count = 0
        ungrounded_count = 0
        total_score = 0.0
        
        # 2. Process each claim
        for claim in claims:
            try:
                updated_claim = await enforce_citation(claim, str(report_id))
                await updated_claim.save()
                
                processed_count += 1
                if updated_claim.grounded:
                    grounded_count += 1
                else:
                    ungrounded_count += 1
                total_score += updated_claim.evidence_score
                
            except Exception as e:
                logger.error(f"Failed to enforce citation for claim {claim.id}: {e}")
                continue

        avg_score = total_score / processed_count if processed_count > 0 else 0.0
        
        proc_time = time.time() - start_time
        logger.info(
            f"Citation enforcement complete for report {report_id}: "
            f"{processed_count} processed, {grounded_count} grounded, "
            f"{ungrounded_count} ungrounded. Avg score: {avg_score:.2f} in {proc_time:.2f}s"
        )
        
        return EnforceCitationsOutput(
            success=True,
            report_id=input_data.report_id,
            claims_processed=processed_count,
            claims_grounded=grounded_count,
            claims_ungrounded=ungrounded_count,
            avg_grounding_score=avg_score,
            processing_time=proc_time
        )
        
    except Exception as e:
        logger.error(f"Error in enforce_citations_command for report {input_data.report_id}: {e}")
        logger.exception(e)
        return EnforceCitationsOutput(
            success=False,
            report_id=input_data.report_id,
            claims_processed=0,
            claims_grounded=0,
            claims_ungrounded=0,
            avg_grounding_score=0.0,
            processing_time=time.time() - start_time,
            error_message=str(e)
        )

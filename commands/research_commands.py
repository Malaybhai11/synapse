import asyncio
import os
import time
from typing import Any, Dict

from loguru import logger
from surreal_commands import CommandInput, CommandOutput, command

from open_notebook.ai.research_orchestrator import run_orchestrated_research
from open_notebook.domain.notebook import GeneratedReport
from open_notebook.ai.confidence_estimator import DEFAULT_CONFIDENCE_VERSION

class RunResearchInput(CommandInput):
    query: str

class RunResearchOutput(CommandOutput):
    success: bool
    report_id: str = ""
    latency_ms: int = 0
    error_message: str = ""

@command(
    "run_orchestrated_research",
    app="open_notebook",
    retry={
        "max_attempts": 2,
        "wait_strategy": "exponential_jitter",
        "wait_min": 2,
        "wait_max": 10,
        "retry_log_level": "debug",
    },
)
async def run_orchestrated_research_command(input_data: RunResearchInput) -> RunResearchOutput:
    """
    Background command that coordinates Phase 8: Parallel Retrieval + Aggregation.
    """
    query = input_data.query
    if not query:
        logger.error("Skipping orchestrated research: No query provided in payload.")
        return RunResearchOutput(success=False, error_message="No query provided")

    logger.info(f"Starting orchestrated research for: '{query}'")
    
    start_time = time.time()
    try:
        # Run the massive parallel engine
        structured_content = await run_orchestrated_research(query)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Persist the output safely mapping to existing schemas
        # Note: Phase 5 Confidence Overwrite is already computed in the orchestrator
        report = GeneratedReport(
            query=query,
            structured_content=structured_content,
            confidence=structured_content.get("confidence", 0.0),
            model_used="orchestrator", # Identifier for tracking
            tokens_used=structured_content.get("metadata", {}).get("orchestrator_token_usage", 0),
            latency_ms=latency_ms,
            schema_version=structured_content.get("version", "1.0"),
            confidence_version=DEFAULT_CONFIDENCE_VERSION,
            generation_status="completed",
        )
        await report.save()
        logger.info(f"Orchestrated GeneratedReport {report.id} saved successfully in {latency_ms}ms.")

        # Phase 4/6 Chaining: Trigger claim extraction
        if os.getenv("SYNAPSE_ENABLE_CLAIM_INGESTION", "true").lower() == "true":
            from surreal_commands import submit_command
            logger.info(f"Enqueuing extract_claims job for report {report.id}")
            submit_command("open_notebook", "extract_claims", {"report_id": str(report.id)})
        else:
            logger.info("Skipped extract_claims: SYNAPSE_ENABLE_CLAIM_INGESTION is disabled.")

        return RunResearchOutput(
            success=True,
            report_id=str(report.id),
            latency_ms=latency_ms
        )
            
    except TimeoutError as e:
        logger.error(f"Orchestration timed out: {e}")
        return RunResearchOutput(success=False, error_message=str(e))
    except Exception as e:
        logger.error(f"Failed to orchestrate research for query '{query}': {e}")
        return RunResearchOutput(success=False, error_message=str(e))


import time
from typing import Optional

from loguru import logger
from surreal_commands import CommandInput, CommandOutput, command

from open_notebook.database.repository import ensure_record_id, repo_query
from open_notebook.domain.notebook import Claim, GeneratedReport
from open_notebook.ai.claim_extractor import process_report_for_claims
from open_notebook.ai.confidence_estimator import estimate_claim_confidence, DEFAULT_CONFIDENCE_VERSION
from open_notebook.utils.embedding import generate_embeddings
import math
import os

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

def passes_linguistic_guard(text: str) -> bool:
    """Rejects claims that are obvious compound statements."""
    conjunctions = [" and ", " but ", " however ", " although ", " nevertheless ", " whereas "]
    count = sum(text.lower().count(c) for c in conjunctions)
    return count <= 1  # 1 tolerance for standard phrasing

class ExtractClaimsInput(CommandInput):
    report_id: str

class ExtractClaimsOutput(CommandOutput):
    success: bool
    report_id: str
    claims_extracted: int
    processing_time: float
    error_message: Optional[str] = None

@command(
    "extract_claims",
    app="open_notebook",
    retry={
        "max_attempts": 3,
        "wait_strategy": "exponential_jitter",
        "wait_min": 1,
        "wait_max": 30,
        "stop_on": [ValueError],  # Don't retry validation or permanent logic errors
        "retry_log_level": "debug",
    },
)
async def extract_claims_command(input_data: ExtractClaimsInput) -> ExtractClaimsOutput:
    """
    Background job to safely extract, batch-embed, and persist atomic claims
    from a generated ResearchReport. Strongly idempotent and capped.
    """
    start_time = time.time()
    try:
        report_id = ensure_record_id(input_data.report_id)
        
        # 1. Load the GeneratedReport object (Idempotency Check via robust status field)
        report = await GeneratedReport.get(str(report_id))
        if not report:
            raise ValueError(f"Report {report_id} not found in database.")
            
        if report.claim_extraction_status == "complete":
            logger.info(f"Claims already fully extracted for report {report_id}. Aborting (Idempotent success).")
            return ExtractClaimsOutput(
                success=True, 
                report_id=input_data.report_id, 
                claims_extracted=0, 
                processing_time=time.time() - start_time
            )
            
        if not report.structured_content:
            report.claim_extraction_status = "failed"
            await report.save()
            raise ValueError(f"Report {report_id} contains no structured JSON content.")
            
        # Explicit Running State
        report.claim_extraction_status = "running"
        await report.save()
            
        logger.info(f"Initiating claim extraction for report {report_id}...")

        # 3. Extract Claims safely (utilizes max extraction caps natively)
        raw_claims = await process_report_for_claims(report.structured_content)
        
        # 3b. Linguistic Form Guard
        valid_claims = []
        for c in raw_claims:
            if passes_linguistic_guard(c["text"]):
                valid_claims.append(c)
            else:
                logger.debug(f"Discarding non-atomic claim (linguistic failure): {c['text']}")

        if not valid_claims:
            logger.info(f"No valid atomic claims found for report {report_id} post-filtering.")
            report.claim_extraction_status = "complete"
            await report.save()
            return ExtractClaimsOutput(
                success=True,
                report_id=input_data.report_id,
                claims_extracted=0,
                processing_time=time.time() - start_time
            )
            
        # 4. Batch Embeddings (Massive latency and cost savings vs per-claim jobs)
        logger.debug(f"Batch embedding {len(valid_claims)} claims...")
        texts_to_embed = [c["text"] for c in valid_claims]
        embeddings = await generate_embeddings(texts_to_embed)
        
        if len(embeddings) != len(valid_claims):
            raise ValueError("Mismatched embedding generation sizes.")

        # 4b. Vector Deduplication (In-Memory Batch Cross-Similarity)
        unique_claims = []
        unique_embeddings = []
        for i, emb in enumerate(embeddings):
            is_dup = False
            for u_emb in unique_embeddings:
                if cosine_similarity(emb, u_emb) > 0.88:
                    is_dup = True
                    break
            if not is_dup:
                unique_claims.append(valid_claims[i])
                unique_embeddings.append(emb)
            else:
                logger.debug(f"Discarding duplicative claim (semantic match > 88%): {valid_claims[i]['text']}")

        # 5. Persist Unique Claims to Database
        saved_claims = 0
        for i, c_dict in enumerate(unique_claims):
            c_dict["report_id"] = str(report_id)
            c_dict["embedding"] = unique_embeddings[i]
            
            # Phase 5 Confidence Mapping
            structured_conf = estimate_claim_confidence(c_dict, report.structured_content)
            
            # Subtly backup AI guess
            naive_conf = c_dict.get("confidence", 0.75)
            c_dict["confidence"] = structured_conf
            c_dict["confidence_version"] = DEFAULT_CONFIDENCE_VERSION
            c_dict["model_confidence"] = naive_conf
            
            # Use Pydantic casting natively on object model init
            claim = Claim(**c_dict)
            
            await claim.save()
            saved_claims += 1
            
        # Conclude state
        report.claim_extraction_status = "complete"
        await report.save()
        
        proc_time = time.time() - start_time
        logger.info(f"Successfully extracted, deduplicated, and embedded {saved_claims} atomic claims for report {report_id} in {proc_time:.2f}s")
        
        return ExtractClaimsOutput(
            success=True,
            report_id=input_data.report_id,
            claims_extracted=saved_claims,
            processing_time=proc_time
        )
        
    except ValueError as e:
        logger.error(f"Permanent failure extracting claims for {input_data.report_id}: {e}")
        # Explicit Failure Check logic integration on known bounded errors
        try:
            report_fail_target = await GeneratedReport.get(str(input_data.report_id))
            if report_fail_target:
                report_fail_target.claim_extraction_status = "failed"
                await report_fail_target.save()
        except:
            pass
        
        return ExtractClaimsOutput(
            success=False,
            report_id=input_data.report_id,
            claims_extracted=0,
            processing_time=time.time() - start_time,
            error_message=str(e),
        )
    except Exception as e:
        # Transparent transient error hand-off to retry bounds
        logger.debug(f"Transient error extracting claims for {input_data.report_id}: {e}")
        try:
            report_fail_target = await GeneratedReport.get(str(input_data.report_id))
            if report_fail_target:
                report_fail_target.claim_extraction_status = "failed"
                await report_fail_target.save()
        except:
            pass
        raise
    finally:
        # Step 6: Chain Citation Enforcement
        if os.getenv("SYNAPSE_ENABLE_CLAIM_INGESTION", "true").lower() == "true":
            from surreal_commands import submit_command
            submit_command("open_notebook", "enforce_citations", {"report_id": str(input_data.report_id)})
            logger.info(f"Chained enforce_citations for report {input_data.report_id}")

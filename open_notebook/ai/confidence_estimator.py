"""
Confidence Estimator Service

Provides strictly pure mathematical functions for assessing evidence reliability natively.
Replaces unbounded logs or sigmoid curves with hard-capped, predictable normalized blends.
Algorithms are deterministic, versioned, and decouple model self-assessment from actual 
evidence density mapping.

VERSIONING: Stores the version string alongside data, permitting safe future ML migrations.
"""

import math
from typing import Dict, Any, List

DEFAULT_CONFIDENCE_VERSION = "baseline_v1"

def _clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(value, max_val))

def calculate_report_confidence(source_count: int, avg_source_score: float, model_confidence: float) -> float:
    """
    Computes report-level confidence.
    Source Density serves as the primary axis of reliability (0.5), over score (0.4) and model hallucination (0.1).
    """
    normalized_density = min(source_count / 10.0, 1.0)
    normalized_score = _clamp(avg_source_score, 0.0, 1.0)
    normalized_model_conf = _clamp(model_confidence, 0.0, 1.0)
    
    raw = (normalized_density * 0.5) + (normalized_score * 0.4) + (normalized_model_conf * 0.1)
    
    return _clamp(raw, 0.1, 0.95)

def calculate_claim_confidence(local_source_count: int, local_avg_score: float, model_confidence: float) -> float:
    """
    Computes claim-level confidence purely off local backing.
    A single claim backed by 3 high-tier sources is effectively fully saturated (local max threshold = 3).
    """
    normalized_density = min(local_source_count / 3.0, 1.0)
    normalized_score = _clamp(local_avg_score, 0.0, 1.0)
    normalized_model_conf = _clamp(model_confidence, 0.0, 1.0)
    
    raw = (normalized_density * 0.5) + (normalized_score * 0.4) + (normalized_model_conf * 0.1)
    
    return _clamp(raw, 0.1, 0.95)

def estimate_report_confidence(report_json: Dict[str, Any]) -> float:
    """
    Parses a research report payload and orchestrates the confidence calculation.
    """
    sources = report_json.get("sources", [])
    source_count = len(sources)
    
    avg_score = 0.0
    if source_count > 0:
        total_score = sum([src.get("score", 0.0) for src in sources])
        avg_score = total_score / source_count
        
    model_conf = report_json.get("confidence", 0.75) # Default LLM blind guess baseline
    
    return calculate_report_confidence(source_count, avg_score, model_conf)

def estimate_claim_confidence(claim_dict: Dict[str, Any], report_json: Dict[str, Any]) -> float:
    """
    Parses an extracted claim dictionary, looks up its specific backing source references
    inside the parent report payload, and isolates the local confidence calculation.
    """
    source_id = str(claim_dict.get("source_id", "unknown"))
    
    # Isolate strictly to the resources proving THIS specific claim
    local_sources = [src for src in report_json.get("sources", []) if str(src.get("doc_id", "")) == source_id]
    local_count = len(local_sources)
    
    local_avg_score = 0.0
    if local_count > 0:
        total_score = sum([src.get("score", 0.0) for src in local_sources])
        local_avg_score = total_score / local_count
        
    model_conf = claim_dict.get("confidence", 0.75)
    
    return calculate_claim_confidence(local_count, local_avg_score, model_conf)

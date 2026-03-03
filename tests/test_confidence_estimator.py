import pytest
from open_notebook.ai.confidence_estimator import (
    calculate_report_confidence,
    calculate_claim_confidence,
    estimate_report_confidence,
    estimate_claim_confidence,
)

def test_extreme_case_report_confidence():
    """Verify 0 sources, 0 score, 0 model conf floors correctly at 0.1"""
    conf = calculate_report_confidence(0, 0.0, 0.0)
    assert conf == 0.1
    
    # Using JSON
    report_json = {
        "sources": [],
        "confidence": 0.0
    }
    assert estimate_report_confidence(report_json) == 0.1

def test_high_evidence_report_confidence():
    """Verify massive evidence hits the ceiling properly at 0.95 without exploding"""
    conf = calculate_report_confidence(50, 1.0, 1.0) # max sources, max score, max conf
    assert conf == 0.95
    
    report_json = {
        "sources": [{"score": 1.0} for _ in range(50)],
        "confidence": 1.0
    }
    assert estimate_report_confidence(report_json) == 0.95

def test_stability_smooth_variance():
    """Verify scaling sources adds linear confidence mapping (stable variance vs sigmoid jump)"""
    # Base Model Only = 0.1 raw
    # Score 0.5 = +0.2 raw
    # Total = 0.3 raw
    
    # Source density logic: min(source_count / 10, 1.0) * 0.5
    conf_8 = calculate_report_confidence(8, 0.5, 1.0)
    # raw = (0.8 * 0.5) + (0.5 * 0.4) + (1.0 * 0.1)
    # raw = 0.4 + 0.2 + 0.1 = 0.7
    assert abs(conf_8 - 0.7) < 0.01

    conf_9 = calculate_report_confidence(9, 0.5, 1.0)
    # raw = (0.9 * 0.5) + (0.5 * 0.4) + (1.0 * 0.1) = 0.45 + 0.2 + 0.1 = 0.75
    assert abs(conf_9 - 0.75) < 0.01
    
    # Difference is exact and smooth (0.05 step per source)
    assert abs((conf_9 - conf_8) - 0.05) < 0.01

def test_claim_local_evidence_mapping():
    """Verify claims ONLY inherit backing from matching source_ids in the overarching report."""
    report_json = {
        "sources": [
            {"doc_id": "doc1", "score": 1.0},
            {"doc_id": "doc1", "score": 0.9},
            {"doc_id": "doc2", "score": 0.2}, 
            {"doc_id": "doc3", "score": 0.1}
        ]
    }
    
    # Claim points only to the highly rated 'doc1' sources (2 count, avg .95)
    claim_dict = {
        "text": "X is Y",
        "source_id": "doc1",
        "confidence": 1.0
    }
    
    conf = estimate_claim_confidence(claim_dict, report_json)
    
    # density = min(2 / 3.0, 1.0) * 0.5 = 0.333
    # score = 0.95 * 0.4 = 0.38
    # model = 1.0 * 0.1 = 0.10
    # raw = 0.333 + 0.38 + 0.10 = 0.813
    assert abs(conf - 0.813) < 0.01

    # Bad claim points to the poor 'doc3' source (1 count, avg .1)
    claim_dict_bad = {
        "source_id": "doc3",
        "confidence": 1.0
    }
    bad_conf = estimate_claim_confidence(claim_dict_bad, report_json)
    
    # density = min(1 / 3.0, 1.0) * 0.5 = 0.166
    # score = 0.1 * 0.4 = 0.04
    # model = 1.0 * 0.1 = 0.10
    # raw = 0.166 + 0.04 + 0.1 = 0.306
    assert abs(bad_conf - 0.306) < 0.01

    # Prove local decoupling (the good claim is massively more confident than the bad claim
    # despite coming from the exact same monolithic report).
    assert conf > bad_conf + 0.5

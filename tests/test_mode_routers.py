from unittest.mock import AsyncMock, patch

import pytest

from api.routers import hypothesis, mode_utils, validator
from api.routers.mode_utils import ContextDocument


class FakeModel:
    def __init__(self, model_type: str = "language"):
        self.type = model_type


def _language_model(*args, **kwargs):
    return FakeModel("language")


@pytest.mark.asyncio
@patch("api.routers.hypothesis.model_manager.get_embedding_model", new_callable=AsyncMock)
@patch("api.routers.hypothesis.Model.get", new_callable=AsyncMock)
@patch("api.routers.hypothesis.call_llm", new_callable=AsyncMock)
@patch("api.routers.hypothesis.gather_context_documents", new_callable=AsyncMock)
async def test_hypothesis_mode_preserves_source_provenance_and_clamps_scores(
    mock_context,
    mock_call_llm,
    mock_model_get,
    mock_embedding_model,
):
    mock_embedding_model.return_value = object()
    mock_model_get.side_effect = _language_model
    mock_context.return_value = [
        ContextDocument(
            id="nb-1",
            sourceType="notebook",
            title="Notebook Source",
            snippet="Internal evidence snippet",
        ),
        ContextDocument(
            id="web-1",
            sourceType="web",
            title="Web Source",
            snippet="External evidence snippet",
            url="https://example.com/source",
        ),
    ]
    mock_call_llm.side_effect = [
        '[{"id":"nb-1","score":120},{"id":"web-1","score":61},{"id":"missing","score":50}]',
        '[{"id":"web-1","score":-10}]',
        "Supporting evidence is stronger than the opposing case.",
    ]

    response = await hypothesis.evaluate_hypothesis(
        hypothesis.HypothesisRequest(
            query="Will the launch succeed?",
            includeWebSearch=True,
            models=hypothesis.HypothesisModelsInput(
                proponentModel="model:1",
                opponentModel="model:2",
                judgeModel="model:3",
            ),
        )
    )

    assert response.proponentEvidence == [
        hypothesis.EvidenceItem(
            id="nb-1",
            sourceType="notebook",
            title="Notebook Source",
            snippet="Internal evidence snippet",
            score=100.0,
        ),
        hypothesis.EvidenceItem(
            id="web-1",
            sourceType="web",
            title="Web Source",
            snippet="External evidence snippet",
            url="https://example.com/source",
            score=61.0,
        ),
    ]
    assert response.opponentEvidence == [
        hypothesis.EvidenceItem(
            id="web-1",
            sourceType="web",
            title="Web Source",
            snippet="External evidence snippet",
            url="https://example.com/source",
            score=0.0,
        )
    ]
    assert response.confidenceScore == 95


@pytest.mark.asyncio
@patch("api.routers.hypothesis.model_manager.get_embedding_model", new_callable=AsyncMock)
@patch("api.routers.hypothesis.Model.get", new_callable=AsyncMock)
@patch("api.routers.hypothesis.gather_context_documents", new_callable=AsyncMock)
async def test_hypothesis_mode_returns_neutral_result_without_context(
    mock_context,
    mock_model_get,
    mock_embedding_model,
):
    mock_embedding_model.return_value = object()
    mock_model_get.side_effect = _language_model
    mock_context.return_value = []

    response = await hypothesis.evaluate_hypothesis(
        hypothesis.HypothesisRequest(
            query="Is there evidence?",
            includeWebSearch=False,
            models=hypothesis.HypothesisModelsInput(
                proponentModel="model:1",
                opponentModel="model:2",
                judgeModel="model:3",
            ),
        )
    )

    assert response.confidenceScore == 50
    assert response.proponentEvidence == []
    assert response.opponentEvidence == []
    assert "remains unverified" in response.judgeSynthesis


@pytest.mark.asyncio
@patch("api.routers.validator.model_manager.get_embedding_model", new_callable=AsyncMock)
@patch("api.routers.validator.Model.get", new_callable=AsyncMock)
@patch("api.routers.validator.call_llm", new_callable=AsyncMock)
@patch("api.routers.validator.gather_context_documents", new_callable=AsyncMock)
async def test_validator_mode_normalizes_enums_and_risk_scores(
    mock_context,
    mock_call_llm,
    mock_model_get,
    mock_embedding_model,
):
    mock_embedding_model.return_value = object()
    mock_model_get.side_effect = _language_model
    mock_context.return_value = [
        ContextDocument(
            id="nb-1",
            sourceType="notebook",
            title="Architecture Notes",
            snippet="The system depends on one engineer for deployments.",
        )
    ]
    mock_call_llm.side_effect = [
        '```json\n[{"description":"A single person can support operations."}]\n```',
        (
            '[{"title":"Key Person Risk","description":"Operations depend on one engineer.",'
            '"severity":"high","score":150},'
            '{"title":"Monitoring Gap","description":"The rollout lacks alerting.",'
            '"severity":"critical","score":20}]'
        ),
        '[{"description":"Document and automate deployments.","effort":"low"},'
        '{"description":"Add basic alerting before launch.","effort":"unknown"}]',
    ]

    response = await validator.evaluate_validator(
        validator.ValidatorRequest(
            idea="Ship the product with a very small operations team.",
            sourceType="both",
            models=validator.ValidatorModelsInput(
                analyzerModel="model:1",
                redTeamModel="model:2",
                strategistModel="model:3",
            ),
        )
    )

    assert response.assumptions == [
        validator.Assumption(description="A single person can support operations.")
    ]
    assert response.vulnerabilities == [
        validator.Vulnerability(
            title="Key Person Risk",
            description="Operations depend on one engineer.",
            severity="High",
            score=100,
        ),
        validator.Vulnerability(
            title="Monitoring Gap",
            description="The rollout lacks alerting.",
            severity="High",
            score=20,
        ),
    ]
    assert response.mitigations == [
        validator.Mitigation(
            description="Document and automate deployments.",
            effort="Low",
        ),
        validator.Mitigation(
            description="Add basic alerting before launch.",
            effort="Medium",
        ),
    ]
    assert response.overallRiskScore == 60


def test_parse_json_array_ignores_trailing_json_object():
    raw_output = (
        '[{"description":"Document and automate deployments.","effort":"low"}]\n'
        '{"risk_score": 82, "rationale": "High operational concentration."}'
    )

    assert mode_utils.parse_json_array(raw_output, fallback=[]) == [
        {
            "description": "Document and automate deployments.",
            "effort": "low",
        }
    ]


@pytest.mark.asyncio
@patch("api.routers.mode_utils.vector_search", new_callable=AsyncMock)
async def test_context_documents_use_vector_search_matches_and_similarity(
    mock_vector_search,
):
    mock_vector_search.return_value = [
        {
            "title": "Vector Result",
            "matches": ["Relevant chunk one.", "Relevant chunk two."],
            "similarity": 0.87,
        }
    ]

    documents = await mode_utils.gather_context_documents(
        "relevant query",
        include_notebook=True,
        include_web=False,
    )

    assert documents == [
        ContextDocument(
            id="nb-1",
            sourceType="notebook",
            title="Vector Result",
            snippet="Relevant chunk one. Relevant chunk two.",
            retrievalScore=0.87,
        )
    ]


def test_validator_defaults_missing_scores_from_severity():
    vulnerabilities = validator._build_vulnerabilities(
        [
            {
                "title": "Data Loss",
                "description": "A critical migration path has no rollback plan.",
                "severity": "critical",
            },
            {
                "title": "UI Polish",
                "description": "A cosmetic edge case remains.",
                "severity": "minor",
            },
        ]
    )

    assert vulnerabilities == [
        validator.Vulnerability(
            title="Data Loss",
            description="A critical migration path has no rollback plan.",
            severity="High",
            score=85,
        ),
        validator.Vulnerability(
            title="UI Polish",
            description="A cosmetic edge case remains.",
            severity="Low",
            score=25,
        ),
    ]

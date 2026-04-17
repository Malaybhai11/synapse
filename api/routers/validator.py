import json
import re
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from api.routers.mode_utils import (
    call_llm,
    clamp_score,
    extract_think,
    gather_context_documents,
    normalize_enum,
    parse_json_array,
    serialize_context_documents,
)
from open_notebook.ai.models import Model, model_manager

router = APIRouter()


class ValidatorModelsInput(BaseModel):
    analyzerModel: str
    redTeamModel: str
    strategistModel: str


class ValidatorRequest(BaseModel):
    idea: str
    sourceType: Literal["notebook", "web", "both"]
    models: ValidatorModelsInput


class Assumption(BaseModel):
    description: str


class Vulnerability(BaseModel):
    title: str
    description: str
    severity: Literal["High", "Medium", "Low"]
    score: int


class Mitigation(BaseModel):
    description: str
    effort: Literal["High", "Medium", "Low"]


class ValidatorResponse(BaseModel):
    idea: str
    assumptions: List[Assumption]
    vulnerabilities: List[Vulnerability]
    mitigations: List[Mitigation]
    overallRiskScore: int
    analyzerThink: Optional[str] = None
    redTeamThink: Optional[str] = None
    strategistThink: Optional[str] = None


ANALYZER_PROMPT = """You are the Analyzer.

Break the idea into the core assumptions that must hold true.
Return ONLY a JSON array. Each item must be:
{"description":"..."}

Rules:
- Use the provided idea and evidence only.
- Keep assumptions concrete and decision-relevant.
- If the evidence is sparse, still identify the most important assumptions implied by the idea.
"""


RED_TEAM_PROMPT = """You are the Red Team.

Attack the idea and assumptions using only the provided evidence.
Return ONLY a JSON array. Each item must be:
{"title":"...","description":"...","severity":"High|Medium|Low","score":0-100}

Rules:
- Focus on concrete failure modes, hidden dependencies, and edge cases.
- Prefer a shorter list of high-signal vulnerabilities over generic filler.
- Scores represent risk severity, not confidence.
"""


STRATEGIST_PROMPT = """You are the Strategist.

You will receive an idea and a list of vulnerabilities.
Return ONLY a JSON array. Each item must be:
{"description":"...","effort":"High|Medium|Low"}

Rules:
- Suggest practical mitigations tied to the stated vulnerabilities.
- Do not restate the problem without proposing an action.

IMPORTANT: After the mitigation array, provide an overall risk assessment as a JSON object:
{"risk_score": 0-100, "rationale": "brief explanation"}

The risk_score should reflect:
- Severity and likelihood of vulnerabilities (0-50 points)
- Number of critical/high severity issues (0-30 points)
- Ease of exploitation and attack surface (0-20 points)
"""


SEVERITY_SCORE_DEFAULTS = {
    "High": 85.0,
    "Medium": 55.0,
    "Low": 25.0,
}


async def _validate_language_model(model_id: str, field_name: str) -> None:
    try:
        model = await Model.get(model_id)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} model {model_id} not found",
        ) from exc

    if model.type != "language":
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} model {model_id} must be a language model",
        )


def _build_assumptions(items: list[dict]) -> list[Assumption]:
    assumptions: list[Assumption] = []
    seen: set[str] = set()
    for item in items:
        description = str(item.get("description", "")).strip()
        if not description or description in seen:
            continue
        seen.add(description)
        assumptions.append(Assumption(description=description))
    return assumptions


def _build_vulnerabilities(items: list[dict]) -> list[Vulnerability]:
    vulnerabilities: list[Vulnerability] = []
    seen: set[tuple[str, str]] = set()

    for item in items:
        title = str(item.get("title", "Risk")).strip() or "Risk"
        description = str(item.get("description", "")).strip()
        if not description:
            continue
        severity = _normalize_severity(item.get("severity"))
        key = (title, description)
        if key in seen:
            continue
        seen.add(key)
        vulnerabilities.append(
            Vulnerability(
                title=title,
                description=description,
                severity=severity,
                score=int(
                    round(
                        clamp_score(
                            item.get("score"),
                            default=SEVERITY_SCORE_DEFAULTS[severity],
                        )
                    )
                ),
            )
        )

    vulnerabilities.sort(key=lambda item: item.score, reverse=True)
    return vulnerabilities


def _normalize_severity(value: object) -> Literal["High", "Medium", "Low"]:
    raw_value = str(value or "").strip().lower()
    if raw_value in {"critical", "severe", "high", "major", "blocker"}:
        return "High"
    if raw_value in {"medium", "moderate", "mid"}:
        return "Medium"
    if raw_value in {"low", "minor", "small", "minimal"}:
        return "Low"
    return "Medium"


def _build_mitigations(items: list[dict]) -> list[Mitigation]:
    mitigations: list[Mitigation] = []
    seen: set[str] = set()
    for item in items:
        description = str(item.get("description", "")).strip()
        if not description or description in seen:
            continue
        seen.add(description)
        mitigations.append(
            Mitigation(
                description=description,
                effort=normalize_enum(
                    item.get("effort"),
                    ("High", "Medium", "Low"),
                    "Medium",
                ),
            )
        )
    return mitigations


def _parse_strategist_risk_score(strategist_content: str) -> int | None:
    match = re.search(r'"risk_score"\s*:\s*(\d+(?:\.\d+)?)', strategist_content)
    if match:
        return int(round(clamp_score(match.group(1))))
    match = re.search(
        r"risk_score[:\s]+(\d+(?:\.\d+)?)",
        strategist_content,
        re.IGNORECASE,
    )
    if match:
        return int(round(clamp_score(match.group(1))))
    return None


def _calculate_overall_risk(
    vulnerabilities: list[Vulnerability],
    strategist_risk_score: int | None = None,
) -> int:
    if not vulnerabilities:
        return int(round(clamp_score(strategist_risk_score, default=0.0)))

    severity_weights = {"High": 1.0, "Medium": 0.6, "Low": 0.3}
    weighted_scores = []
    for vuln in vulnerabilities[:5]:
        weight = severity_weights.get(vuln.severity, 0.6)
        weighted_scores.append(vuln.score * weight)

    if not weighted_scores:
        return 0

    vulnerability_risk = sum(weighted_scores) / len(weighted_scores)
    if strategist_risk_score is not None:
        risk_score = (vulnerability_risk * 0.75) + (strategist_risk_score * 0.25)
    else:
        risk_score = vulnerability_risk

    return int(round(clamp_score(risk_score, default=0.0)))


@router.post("/evaluate", response_model=ValidatorResponse)
async def evaluate_validator(request: ValidatorRequest):
    try:
        await _validate_language_model(
            request.models.analyzerModel, "Analyzer"
        )
        await _validate_language_model(
            request.models.redTeamModel, "Red Team"
        )
        await _validate_language_model(
            request.models.strategistModel, "Strategist"
        )

        include_notebook = request.sourceType in {"notebook", "both"}
        include_web = request.sourceType in {"web", "both"}

        if include_notebook and not await model_manager.get_embedding_model():
            raise HTTPException(
                status_code=400,
                detail="Critique mode requires an embedding model for notebook retrieval.",
            )

        context_documents = await gather_context_documents(
            request.idea,
            include_notebook=include_notebook,
            include_web=include_web,
        )
        context_json = serialize_context_documents(context_documents)

        analyzer_query = (
            f"Idea:\n{request.idea.strip()}\n\n"
            f"Evidence candidates:\n{context_json}"
        )
        analyzer_raw = await call_llm(
            request.models.analyzerModel,
            ANALYZER_PROMPT,
            analyzer_query,
        )
        analyzer_think, analyzer_content = extract_think(analyzer_raw)
        assumptions = _build_assumptions(
            parse_json_array(
                analyzer_content,
                fallback=[{"description": "The proposal depends on unstated assumptions."}],
            )
        )

        red_team_query = (
            f"Idea:\n{request.idea.strip()}\n\n"
            f"Assumptions:\n{json.dumps([item.model_dump() for item in assumptions], ensure_ascii=False)}\n\n"
            f"Evidence candidates:\n{context_json}"
        )
        red_team_raw = await call_llm(
            request.models.redTeamModel,
            RED_TEAM_PROMPT,
            red_team_query,
        )
        red_team_think, red_team_content = extract_think(red_team_raw)
        vulnerabilities = _build_vulnerabilities(
            parse_json_array(
                red_team_content,
                fallback=[
                    {
                        "title": "Analysis Error",
                        "description": "The critique engine could not produce a structured vulnerability list.",
                        "severity": "Medium",
                        "score": 50,
                    }
                ],
            )
        )

        strategist_query = (
            f"Idea:\n{request.idea.strip()}\n\n"
            f"Vulnerabilities:\n{json.dumps([item.model_dump() for item in vulnerabilities], ensure_ascii=False)}"
        )
        strategist_raw = await call_llm(
            request.models.strategistModel,
            STRATEGIST_PROMPT,
            strategist_query,
        )
        strategist_think, strategist_content = extract_think(strategist_raw)
        mitigations = _build_mitigations(
            parse_json_array(
                strategist_content,
                fallback=[
                    {
                        "description": "Re-run the critique with more concrete scope and success criteria.",
                        "effort": "Low",
                    }
                ],
            )
        )

        strategist_risk_score = _parse_strategist_risk_score(strategist_content)

        return ValidatorResponse(
            idea=request.idea.strip(),
            assumptions=assumptions,
            vulnerabilities=vulnerabilities,
            mitigations=mitigations,
            overallRiskScore=_calculate_overall_risk(vulnerabilities, strategist_risk_score),
            analyzerThink=analyzer_think,
            redTeamThink=red_team_think,
            strategistThink=strategist_think,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Validator evaluation failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

import re
from typing import Any, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from api.routers.mode_utils import (
    ContextDocument,
    call_llm,
    clamp_score,
    extract_think,
    gather_context_documents,
    parse_json_array,
    serialize_context_documents,
)
from open_notebook.ai.models import Model, model_manager

router = APIRouter()


class HypothesisModelsInput(BaseModel):
    proponentModel: str
    opponentModel: str
    judgeModel: str


class HypothesisRequest(BaseModel):
    query: str
    includeWebSearch: Optional[bool] = False
    models: HypothesisModelsInput


class EvidenceItem(BaseModel):
    id: str
    sourceType: Literal["notebook", "web"]
    title: str
    snippet: str
    url: Optional[str] = None
    score: float


class HypothesisResponse(BaseModel):
    hypothesis: str
    confidenceScore: int
    proponentEvidence: List[EvidenceItem]
    opponentEvidence: List[EvidenceItem]
    proponentThink: Optional[str] = None
    opponentThink: Optional[str] = None
    judgeSynthesis: str
    judgeThink: Optional[str] = None


SELECTION_PROMPT = """You are reviewing evidence candidates for a hypothesis debate.

Return ONLY a JSON array. Each item must be:
{"id":"candidate-id","score":0-100}

Rules:
- Use only candidate IDs that appear in the provided evidence list.
- Do not invent titles, snippets, URLs, or IDs.
- Select only evidence that clearly matches the requested stance.
- If no evidence qualifies, return [].
- Scores represent how strongly the selected evidence supports the requested stance.
"""


JUDGE_PROMPT = """You are the judge in a structured hypothesis review.

Use ONLY the provided hypothesis and evidence selections.
- Do not invent facts or sources.
- If evidence is weak or mixed, say that directly.
- Write a concise synthesis that explains what the current evidence supports, what it does not, and why the confidence ended where it did.

IMPORTANT: After your synthesis, provide a final confidence assessment as a JSON object:
{"confidence": 0-100}

The confidence should reflect:
- Quality and quantity of supporting evidence (0-40 points)
- Quality and quantity of opposing evidence (0-40 points)  
- Overall coherence and plausibility (0-20 points)

A hypothesis with strong evidence on one side and weak on the other should score higher (70-95).
A hypothesis with mixed or weak evidence on both sides should score medium (40-70).
A hypothesis with no clear evidence either way should score low (5-40).
"""


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


def _resolve_evidence(
    raw_items: list[dict],
    documents_by_id: dict[str, ContextDocument],
) -> list[EvidenceItem]:
    evidence_items: list[EvidenceItem] = []
    seen_ids: set[str] = set()
    documents = list(documents_by_id.values())

    for item in raw_items:
        document = _find_document_for_evidence_item(item, documents_by_id, documents)
        if not document or document.id in seen_ids:
            continue
        seen_ids.add(document.id)
        evidence_items.append(
            EvidenceItem(
                id=document.id,
                sourceType=document.sourceType,
                title=document.title,
                snippet=document.snippet,
                url=document.url,
                score=clamp_score(item.get("score")),
            )
        )

    evidence_items.sort(key=lambda item: item.score, reverse=True)
    return evidence_items


def _normalized_match_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _find_document_for_evidence_item(
    item: dict,
    documents_by_id: dict[str, ContextDocument],
    documents: list[ContextDocument],
) -> ContextDocument | None:
    for key in ("id", "candidate_id", "candidateId", "source_id", "sourceId"):
        candidate_id = str(item.get(key, "")).strip()
        if candidate_id in documents_by_id:
            return documents_by_id[candidate_id]

    item_title = _normalized_match_text(item.get("title"))
    item_url = _normalized_match_text(item.get("url"))
    item_snippet = _normalized_match_text(item.get("snippet"))

    for document in documents:
        if item_url and item_url == _normalized_match_text(document.url):
            return document
        if item_title and item_title == _normalized_match_text(document.title):
            return document
        document_snippet = _normalized_match_text(document.snippet)
        if item_snippet and (
            item_snippet in document_snippet or document_snippet in item_snippet
        ):
            return document

    return None


def _calculate_confidence(
    supporting_evidence: list[EvidenceItem],
    opposing_evidence: list[EvidenceItem],
) -> int | None:
    support_strength = sum(item.score for item in supporting_evidence[:5])
    oppose_strength = sum(item.score for item in opposing_evidence[:5])
    total_strength = support_strength + oppose_strength

    if total_strength <= 0:
        return None

    support_delta = (support_strength - oppose_strength) / total_strength
    damped_confidence = 50 + (support_delta * 45)
    return int(round(max(5, min(95, damped_confidence))))


def _parse_judge_confidence(judge_content: str) -> int | None:
    match = re.search(r'"confidence"\s*:\s*(\d+(?:\.\d+)?)', judge_content)
    if match:
        return int(round(clamp_score(match.group(1))))
    match = re.search(
        r"confidence[:\s]+(\d+(?:\.\d+)?)",
        judge_content,
        re.IGNORECASE,
    )
    if match:
        return int(round(clamp_score(match.group(1))))
    return None


def _strip_judge_confidence(judge_content: str) -> str:
    without_json = re.sub(
        r"\{[^{}]*\"confidence\"\s*:\s*\d+(?:\.\d+)?[^{}]*\}",
        "",
        judge_content,
        flags=re.IGNORECASE,
    )
    return without_json.strip()


@router.post("/evaluate", response_model=HypothesisResponse)
async def evaluate_hypothesis(request: HypothesisRequest):
    try:
        logger.info(f"Evaluating hypothesis: {request.query}")

        await _validate_language_model(
            request.models.proponentModel, "Proponent"
        )
        await _validate_language_model(
            request.models.opponentModel, "Opponent"
        )
        await _validate_language_model(request.models.judgeModel, "Judge")

        if not await model_manager.get_embedding_model():
            raise HTTPException(
                status_code=400,
                detail="Hypothesis mode requires an embedding model for notebook retrieval.",
            )

        evidence_candidates = await gather_context_documents(
            request.query,
            include_notebook=True,
            include_web=bool(request.includeWebSearch),
        )

        if not evidence_candidates:
            return HypothesisResponse(
                hypothesis=request.query.strip(),
                confidenceScore=50,
                proponentEvidence=[],
                opponentEvidence=[],
                judgeSynthesis=(
                    "No relevant evidence was found in the selected sources, so the "
                    "hypothesis remains unverified."
                ),
            )

        evidence_context = serialize_context_documents(evidence_candidates)
        documents_by_id = {document.id: document for document in evidence_candidates}

        proponent_query = (
            f"Hypothesis:\n{request.query.strip()}\n\n"
            f"Stance:\nSupport the hypothesis.\n\n"
            f"Evidence candidates:\n{evidence_context}"
        )
        proponent_raw = await call_llm(
            request.models.proponentModel,
            SELECTION_PROMPT,
            proponent_query,
        )
        proponent_think, proponent_content = extract_think(proponent_raw)
        proponent_evidence = _resolve_evidence(
            parse_json_array(proponent_content, fallback=[]),
            documents_by_id,
        )

        opponent_query = (
            f"Hypothesis:\n{request.query.strip()}\n\n"
            f"Stance:\nOppose, question, or weaken the hypothesis.\n\n"
            f"Evidence candidates:\n{evidence_context}"
        )
        opponent_raw = await call_llm(
            request.models.opponentModel,
            SELECTION_PROMPT,
            opponent_query,
        )
        opponent_think, opponent_content = extract_think(opponent_raw)
        opponent_evidence = _resolve_evidence(
            parse_json_array(opponent_content, fallback=[]),
            documents_by_id,
        )

        calculated_confidence = _calculate_confidence(proponent_evidence, opponent_evidence)

        judge_query = (
            f"Hypothesis:\n{request.query.strip()}\n\n"
            f"Supporting evidence:\n{serialize_context_documents(proponent_evidence)}\n\n"
            f"Opposing evidence:\n{serialize_context_documents(opponent_evidence)}\n\n"
            f"Calculated confidence score:\n{calculated_confidence if calculated_confidence is not None else 'N/A (no evidence found)'}"
        )
        judge_raw = await call_llm(
            request.models.judgeModel,
            JUDGE_PROMPT,
            judge_query,
        )
        judge_think, judge_content = extract_think(judge_raw)

        judge_confidence = _parse_judge_confidence(judge_content)
        if calculated_confidence is not None:
            confidence = calculated_confidence
        elif judge_confidence is not None:
            confidence = int(round(clamp_score(judge_confidence)))
        else:
            confidence = 50
        judge_synthesis = _strip_judge_confidence(judge_content)

        return HypothesisResponse(
            hypothesis=request.query.strip(),
            confidenceScore=confidence,
            proponentEvidence=proponent_evidence,
            opponentEvidence=opponent_evidence,
            proponentThink=proponent_think,
            opponentThink=opponent_think,
            judgeSynthesis=judge_synthesis or "No synthesis available.",
            judgeThink=judge_think,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Hypothesis evaluation failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

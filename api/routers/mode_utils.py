import json
import re
from collections.abc import Iterable
from typing import Any, Literal, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from pydantic import BaseModel

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.domain.notebook import vector_search

MAX_CONTEXT_ITEMS = 8
MAX_WEB_RESULTS = 5
MAX_SNIPPET_CHARS = 700


class ContextDocument(BaseModel):
    id: str
    sourceType: Literal["notebook", "web"]
    title: str
    snippet: str
    url: Optional[str] = None
    retrievalScore: float = 0.0


def normalize_text(text: Any, *, limit: int = MAX_SNIPPET_CHARS) -> str:
    if isinstance(text, Iterable) and not isinstance(text, (str, bytes, dict)):
        text = " ".join(str(item) for item in text if item)
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3].rstrip()}..."


def extract_think(text: str) -> tuple[Optional[str], str]:
    think_match = re.search(r"<think>(.*?)</think>", text, flags=re.DOTALL)
    if think_match:
        think_text = think_match.group(1).strip()
        main_text = text.replace(think_match.group(0), "").strip()
        return think_text, main_text
    return None, text.strip()


def _extract_balanced_json(raw_text: str, opening: str, closing: str) -> str | None:
    start = raw_text.find(opening)
    if start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False

    for index, char in enumerate(raw_text[start:], start=start):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_string:
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return raw_text[start : index + 1]

    return None


def extract_json_payload(raw_text: str, *, prefer_array: bool = False) -> str:
    payload = str(raw_text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", payload, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        payload = fenced.group(1).strip()

    if prefer_array:
        array_payload = _extract_balanced_json(payload, "[", "]")
        if array_payload:
            return array_payload.strip()

    array_start = payload.find("[")
    object_start = payload.find("{")
    if array_start != -1 and (object_start == -1 or array_start < object_start):
        array_payload = _extract_balanced_json(payload, "[", "]")
        if array_payload:
            return array_payload.strip()
    elif object_start != -1:
        object_payload = _extract_balanced_json(payload, "{", "}")
        if object_payload:
            return object_payload.strip()

    return payload.strip()


def parse_json_array(raw_text: str, fallback: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        payload = extract_json_payload(raw_text, prefer_array=True)
        parsed = json.loads(payload)
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        if isinstance(parsed, dict):
            return [parsed]
    except Exception as exc:
        logger.error(f"Failed to parse JSON array: {exc}\nRaw: {raw_text}")
    return fallback


def clamp_score(value: Any, *, default: float = 50.0) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        numeric_value = default
    return max(0.0, min(100.0, numeric_value))


def normalize_enum(value: Any, allowed: tuple[str, ...], default: str) -> str:
    raw_value = str(value or "").strip().lower()
    for candidate in allowed:
        if raw_value == candidate.lower():
            return candidate
    return default


def result_score(result: dict[str, Any]) -> float:
    return clamp_score(
        result.get("score")
        or result.get("similarity")
        or result.get("relevance")
        or result.get("retrievalScore"),
        default=0.0,
    )


def serialize_context_documents(documents: list[ContextDocument]) -> str:
    return json.dumps(
        [document.model_dump() for document in documents],
        ensure_ascii=False,
        indent=2,
    )


async def call_llm(model_id: str, system_prompt: str, user_prompt: str) -> str:
    try:
        llm = await provision_langchain_model(
            content=user_prompt,
            model_id=model_id,
            default_type="chat",
        )
        response = await llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        return str(response.content)
    except Exception as exc:
        logger.error(f"Error calling LLM {model_id}: {exc}")
        return f"Model Error: {exc}"


async def gather_context_documents(
    query: str,
    *,
    include_notebook: bool,
    include_web: bool,
    notebook_results: int = MAX_CONTEXT_ITEMS,
    web_results: int = MAX_WEB_RESULTS,
) -> list[ContextDocument]:
    documents: list[ContextDocument] = []

    if include_notebook:
        notebook_matches = await vector_search(
            keyword=query,
            results=notebook_results,
            source=True,
            note=True,
            minimum_score=0.2,
        )
        for index, result in enumerate(notebook_matches, start=1):
            snippet = normalize_text(
                result.get("full_text")
                or result.get("content")
                or result.get("matches")
                or result.get("text")
                or result.get("snippet")
            )
            if not snippet:
                continue
            documents.append(
                ContextDocument(
                    id=f"nb-{index}",
                    sourceType="notebook",
                    title=normalize_text(result.get("title") or f"Notebook Evidence {index}", limit=180),
                    snippet=snippet,
                    retrievalScore=result_score(result),
                )
            )

    if include_web:
        try:
            from duckduckgo_search import DDGS

            web_matches = list(DDGS().text(query, max_results=web_results))
        except Exception as exc:
            logger.warning(f"Web search failed: {exc}")
            web_matches = []

        for index, result in enumerate(web_matches, start=1):
            snippet = normalize_text(result.get("body") or result.get("snippet"))
            if not snippet:
                continue
            documents.append(
                ContextDocument(
                    id=f"web-{index}",
                    sourceType="web",
                    title=normalize_text(result.get("title") or f"Web Evidence {index}", limit=180),
                    snippet=snippet,
                    url=result.get("href"),
                    retrievalScore=0.0,
                )
            )

    deduped: list[ContextDocument] = []
    seen = set()
    for document in documents:
        key = (document.sourceType, document.title, document.snippet)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(document)

    return deduped

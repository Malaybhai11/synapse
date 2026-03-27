import json
import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from open_notebook.ai.models import model_manager, Model
from open_notebook.ai.provision import provision_langchain_model
from langchain_core.messages import SystemMessage, HumanMessage
from open_notebook.domain.notebook import vector_search

router = APIRouter()

class ValidatorModelsInput(BaseModel):
    analyzerModel: str
    redTeamModel: str
    strategistModel: str

class ValidatorRequest(BaseModel):
    idea: str
    sourceType: str # "notebook", "web", "both"
    models: ValidatorModelsInput

class Assumption(BaseModel):
    description: str

class Vulnerability(BaseModel):
    title: str
    description: str
    severity: str # "High", "Medium", "Low"
    score: int # 1 - 100

class Mitigation(BaseModel):
    description: str
    effort: str # "High", "Medium", "Low"

class ValidatorResponse(BaseModel):
    idea: str
    assumptions: List[Assumption]
    vulnerabilities: List[Vulnerability]
    mitigations: List[Mitigation]
    overallRiskScore: int
    analyzerThink: Optional[str] = None
    redTeamThink: Optional[str] = None
    strategistThink: Optional[str] = None

async def _gather_notebook_context(query: str) -> str:
    try:
        results = await vector_search(
            keyword=query,
            results=10,
            source=True,
            note=True,
            minimum_score=0.2
        )
        if not results:
            return "No relevant context found in notebooks."
        
        context_parts = []
        for res in results:
            content = res.get("full_text", "") or res.get("content", "")
            title = res.get("title", "Untitled")
            context_parts.append(f"Document [{title}]:\n{content}")
            
        return "\n\n".join(context_parts)
    except Exception as e:
        logger.error(f"Error gathering notebook context: {e}")
        return "Failed to access notebook context."

def _extract_think(text: str) -> tuple[Optional[str], str]:
    think_match = re.search(r'<think>(.*?)</think>', text, flags=re.DOTALL)
    if think_match:
        think_text = think_match.group(1).strip()
        main_text = text.replace(think_match.group(0), "").strip()
        return think_text, main_text
    return None, text.strip()

async def _call_llm(model_id: str, system_prompt: str, user_prompt: str) -> str:
    try:
        llm = await provision_langchain_model(
            content=user_prompt,
            model_id=model_id,
            default_type="chat"
        )
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        return response.content
    except Exception as e:
        logger.error(f"Error calling LLM {model_id}: {e}")
        return f"Model Error: {str(e)}"

def _parse_json_list(raw_text: str, fallback_item: dict) -> list:
    items = []
    try:
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0]
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0]
            
        start = raw_text.find('[')
        end = raw_text.rfind(']')
        if start != -1 and end != -1:
            raw_text = raw_text[start:end+1]
            
        return json.loads(raw_text.strip())
    except Exception as e:
        logger.error(f"Failed to parse json: {e}\nRaw:{raw_text}")
        return [fallback_item]

@router.post("/evaluate", response_model=ValidatorResponse)
async def evaluate_validator(request: ValidatorRequest):
    try:
        # Context gathering
        context = ""
        
        if request.sourceType in ["notebook", "both"]:
            context += f"\n--- INTERNAL KNOWLEDGE BASE ---\n{await _gather_notebook_context(request.idea)}"
            
        if request.sourceType in ["web", "both"]:
            try:
                from duckduckgo_search import DDGS
                results = DDGS().text(request.idea, max_results=5)
                web_context = "\n\n".join([f"Title: {r.get('title')}\nSnippet: {r.get('body')}" for r in results])
                context += f"\n--- WEB SEARCH RESULTS ---\n{web_context}"
            except Exception as e:
                logger.warning(f"Web search failed: {e}")
                context += "\n--- WEB SEARCH RESULTS ---\nFailed to retrieve."

        if not context:
            context = "No external context requested."

        # 1. Analyzer Model
        analyzer_sys = "You are the Analyzer. Break down the user's idea/plan into core assumptions. Output ONLY a valid JSON array of objects with a 'description' field representing an assumption. E.g. [{\"description\": \"Assumption 1\"}]"
        analyzer_query = f"Idea: {request.idea}\n\nContext:\n{context}"
        analyzer_raw = await _call_llm(request.models.analyzerModel, analyzer_sys, analyzer_query)
        analyzer_think, analyzer_content = _extract_think(analyzer_raw)
        
        assumptions = _parse_json_list(
            analyzer_content, 
            {"description": f"Failed to parse assumptions properly. Raw: {analyzer_content[:150]}"}
        )
        
        # 2. Red Team Model
        redteam_sys = "You are the Red Team (Devil's Advocate). Ruthlessly attack the idea and assumptions to find critical vulnerabilities, edge cases, and failure points. Use the context provided. Output ONLY a valid JSON array of objects with 'title', 'description', 'severity' (High, Medium, Low), and 'score' (1-100 severity metric). E.g. [{\"title\": \"...\", \"description\": \"...\", \"severity\": \"High\", \"score\": 90}]"
        redteam_query = f"Idea: {request.idea}\n\nAssumptions:\n{json.dumps(assumptions)}\n\nContext:\n{context}"
        redteam_raw = await _call_llm(request.models.redTeamModel, redteam_sys, redteam_query)
        redteam_think, redteam_content = _extract_think(redteam_raw)
        
        vulnerabilities = _parse_json_list(
            redteam_content,
            {"title": "Analysis Error", "description": "Failed to parse vulnerabilities.", "severity": "Medium", "score": 50}
        )
        
        # 3. Strategist Model
        strategist_sys = "You are the Strategist. You have seen an idea and its vulnerabilities. Suggest concrete, highly actionable mitigations. Output ONLY a valid JSON array of objects with 'description' and 'effort' (High, Medium, Low). E.g. [{\"description\": \"Do UX testing\", \"effort\": \"Low\"}]"
        strategist_query = f"Idea: {request.idea}\n\nVulnerabilities:\n{json.dumps(vulnerabilities)}"
        strategist_raw = await _call_llm(request.models.strategistModel, strategist_sys, strategist_query)
        strategist_think, strategist_content = _extract_think(strategist_raw)
        
        mitigations = _parse_json_list(
            strategist_content,
            {"description": "Failed to parse mitigations.", "effort": "Medium"}
        )
        
        # Risk Score Calc
        if vulnerabilities:
            scores = [int(v.get("score", 0)) for v in vulnerabilities if isinstance(v, dict)]
            overall_risk = int(sum(scores) / len(scores)) if scores else 0
        else:
            overall_risk = 0

        # Create properly typed list for pydantic
        parsed_assumptions = [Assumption(description=str(a.get("description", ""))) for a in assumptions if isinstance(a, dict)]
        parsed_vulns = [Vulnerability(
            title=str(v.get("title", "Risk")),
            description=str(v.get("description", "")),
            severity=str(v.get("severity", "Medium")),
            score=int(v.get("score", 50))
        ) for v in vulnerabilities if isinstance(v, dict)]
        parsed_mits = [Mitigation(
            description=str(m.get("description", "")),
            effort=str(m.get("effort", "Medium"))
        ) for m in mitigations if isinstance(m, dict)]

        return ValidatorResponse(
            idea=request.idea,
            assumptions=parsed_assumptions,
            vulnerabilities=parsed_vulns,
            mitigations=parsed_mits,
            overallRiskScore=overall_risk,
            analyzerThink=analyzer_think,
            redTeamThink=redteam_think,
            strategistThink=strategist_think
        )

    except Exception as e:
        logger.error(f"Validator evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

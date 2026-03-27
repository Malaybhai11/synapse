import json
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from open_notebook.ai.models import model_manager, Model
from open_notebook.ai.provision import provision_langchain_model
from langchain_core.messages import SystemMessage, HumanMessage
from open_notebook.domain.notebook import vector_search

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
    sourceType: str
    title: str
    snippet: str
    url: Optional[str] = None
    score: float

class HypothesisResponse(BaseModel):
    hypothesis: str
    confidenceScore: int
    proponentEvidence: List[EvidenceItem]
    opponentEvidence: List[EvidenceItem]
    judgeSynthesis: str

async def _gather_notebook_context(query: str) -> str:
    """Retrieve context from the user's notebooks via vector search."""
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

async def _call_llm(model_id: str, system_prompt: str, user_prompt: str) -> str:
    """Helper to call LanguageModel via Langchain provisioning."""
    try:
        # Provision a langchain-compatible model instead of calling Esperanto directly
        llm = await provision_langchain_model(
            content=user_prompt,
            model_id=model_id,
            default_type="chat"
        )
        
        # Call it using langchain's ainvoke and our message classes
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        # Langchain response is an AIMessage object with string content
        return response.content
    except Exception as e:
        logger.error(f"Error calling LLM {model_id}: {e}")
        return f"Model Error: {str(e)}"

@router.post("/evaluate", response_model=HypothesisResponse)
async def evaluate_hypothesis(request: HypothesisRequest):
    """Evaluate a hypothesis by orchestrating Proponent, Opponent, and Judge agents."""
    try:
        logger.info(f"Evaluating hypothesis: {request.query}")
        
        # 1. Gather context
        context = await _gather_notebook_context(request.query)
        web_context = ""
        if request.includeWebSearch:
            try:
                from langchain_community.tools import DuckDuckGoSearchRun
                search = DuckDuckGoSearchRun()
                web_context = search.run(request.query)
            except Exception as e:
                logger.warning(f"Web search failed: {e}")
                web_context = "Web search failed or not available."
                
        full_context = f"--- INTERNAL KNOWLEDGE BASE ---\n{context}\n\n--- WEB SEARCH RESULTS ---\n{web_context}"

        # 2. Reformulate Hypothesis
        formal_hypothesis = request.query # Simplifying: could use another LLM call to formalize it.
        
        # 3. Proponent Agent
        proponent_system = "You are the Proponent. Your job is to extract and summarize all evidence that directly SUPPORTS the user's hypothesis. Only use the provided context. Format the output as a JSON list of objects with 'title', 'snippet', and 'score' (1-100)."
        proponent_query = f"Hypothesis: {formal_hypothesis}\n\nContext:\n{full_context}"
        proponent_raw = await _call_llm(request.models.proponentModel, proponent_system, proponent_query)
        
        # 4. Opponent Agent
        opponent_system = "You are the Opponent. Your job is to extract and summarize all evidence that contradicts, questions, or OPPOSES the user's hypothesis. Only use the provided context. Format the output as a JSON list of objects with 'title', 'snippet', and 'score' (1-100)."
        opponent_query = f"Hypothesis: {formal_hypothesis}\n\nContext:\n{full_context}"
        opponent_raw = await _call_llm(request.models.opponentModel, opponent_system, opponent_query)
        
        # Parse JSON securely 
        def _parse_evidence(raw_text, source_type="notebook"):
            items = []
            try:
                # Strip backticks if passed
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0]
                elif "```" in raw_text:
                    raw_text = raw_text.split("```")[1].split("```")[0]
                    
                start = raw_text.find('[')
                end = raw_text.rfind(']')
                if start != -1 and end != -1:
                    raw_text = raw_text[start:end+1]
                    
                data = json.loads(raw_text.strip())
                for idx, item in enumerate(data):
                    items.append(EvidenceItem(
                        id=f"{source_type}_{idx}",
                        sourceType=source_type,
                        title=item.get("title", "Evidence"),
                        snippet=item.get("snippet", str(item)),
                        score=float(item.get("score", 50))
                    ))
            except Exception as e:
                logger.error(f"Failed to parse evidence json: {e}")
                logger.error(f"Raw text: {raw_text}")
                items.append(EvidenceItem(
                    id=f"{source_type}_error",
                    sourceType=source_type,
                    title="Error Parsing Output",
                    snippet=f"The agent returned malformed output. Raw: {str(raw_text)[:150]}...",
                    score=0.0
                ))
            return items
            
        prop_evidence = _parse_evidence(proponent_raw, "notebook")
        opp_evidence = _parse_evidence(opponent_raw, "notebook")
        
        # 5. Judge Agent
        judge_system = "You are the Judge. You will receive a hypothesis, supporting evidence, and opposing evidence. Synthesize a nuanced final paragraph concluding the debate. Do not output json, just the final string."
        judge_query = f"Hypothesis: {formal_hypothesis}\n\nSupporting: {proponent_raw}\n\nOpposing: {opponent_raw}"
        judge_synthesis = await _call_llm(request.models.judgeModel, judge_system, judge_query)
        
        # 6. Calculate Confidence
        prop_score = sum([e.score for e in prop_evidence])
        opp_score = sum([e.score for e in opp_evidence])
        total = prop_score + opp_score
        confidence = int((prop_score / total) * 100) if total > 0 else 50
        
        return HypothesisResponse(
            hypothesis=formal_hypothesis,
            confidenceScore=confidence,
            proponentEvidence=prop_evidence,
            opponentEvidence=opp_evidence,
            judgeSynthesis=judge_synthesis
        )
        
    except Exception as e:
        logger.error(f"Hypothesis evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

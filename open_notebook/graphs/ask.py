import operator
from typing import Annotated, List

from ai_prompter import Prompter
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.domain.notebook import vector_search
from open_notebook.exceptions import OpenNotebookError
from open_notebook.utils import clean_thinking_content
from open_notebook.utils.error_classifier import classify_error
from open_notebook.utils.text_utils import extract_text_content
from open_notebook.ai.validator import OutputSchemaValidator
from open_notebook.ai.confidence_estimator import estimate_report_confidence, DEFAULT_CONFIDENCE_VERSION
from open_notebook.domain.notebook import GeneratedReport
from surreal_commands import submit_command
from loguru import logger
import json
import os


class SubGraphState(TypedDict):
    question: str
    term: str
    instructions: str
    results: dict
    answer: str
    ids: list  # Added for provide_answer function


class Search(BaseModel):
    term: str
    instructions: str = Field(
        description="Tell the answeting LLM what information you need extracted from this search"
    )


class Strategy(BaseModel):
    reasoning: str
    searches: List[Search] = Field(
        default_factory=list,
        description="You can add up to five searches to this strategy",
    )


class ThreadState(TypedDict):
    question: str
    strategy: Strategy
    answers: Annotated[list, operator.add]
    final_answer: str


async def call_model_with_messages(state: ThreadState, config: RunnableConfig) -> dict:
    try:
        parser = PydanticOutputParser(pydantic_object=Strategy)
        system_prompt = Prompter(prompt_template="ask/entry", parser=parser).render(  # type: ignore[arg-type]
            data=state  # type: ignore[arg-type]
        )
        model = await provision_langchain_model(
            system_prompt,
            config.get("configurable", {}).get("strategy_model"),
            "tools",
            max_tokens=2000,
            structured=dict(type="json"),
        )
        # model = model.bind_tools(tools)
        # First get the raw response from the model
        ai_message = await model.ainvoke(system_prompt)

        # Clean the thinking content from the response
        message_content = extract_text_content(ai_message.content)
        cleaned_content = clean_thinking_content(message_content)

        # Parse the cleaned JSON content
        strategy = parser.parse(cleaned_content)

        return {"strategy": strategy}
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


async def trigger_queries(state: ThreadState, config: RunnableConfig):
    return [
        Send(
            "provide_answer",
            {
                "question": state["question"],
                "instructions": s.instructions,
                "term": s.term,
                # "type": s.type,
            },
        )
        for s in state["strategy"].searches
    ]


async def provide_answer(state: SubGraphState, config: RunnableConfig) -> dict:
    try:
        payload = state
        # if state["type"] == "text":
        #     results = text_search(state["term"], 10, True, True)
        # else:
        results = await vector_search(state["term"], 10, True, True)
        if len(results) == 0:
            return {"answers": []}
        payload["results"] = results
        ids = [r["id"] for r in results]
        payload["ids"] = ids
        system_prompt = Prompter(prompt_template="ask/query_process").render(data=payload)  # type: ignore[arg-type]
        model = await provision_langchain_model(
            system_prompt,
            config.get("configurable", {}).get("answer_model"),
            "tools",
            max_tokens=2000,
        )
        ai_message = await model.ainvoke(system_prompt)
        ai_content = extract_text_content(ai_message.content)
        return {"answers": [clean_thinking_content(ai_content)]}
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


async def write_final_answer(state: ThreadState, config: RunnableConfig) -> dict:
    try:
        system_prompt = Prompter(prompt_template="ask/final_answer").render(data=state)  # type: ignore[arg-type]
        model = await provision_langchain_model(
            system_prompt,
            config.get("configurable", {}).get("final_answer_model"),
            "tools",
            max_tokens=2000,
        )
        ai_message = await model.ainvoke(system_prompt)
        final_content = extract_text_content(ai_message.content)
        cleaned_content = clean_thinking_content(final_content)
        
        # Apply strict schema validation if requested in research mode
        run_mode = config.get("configurable", {}).get("mode", "default")
        if run_mode == "research":
            # Determine schema path dynamically to remain robust
            schema_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "schemas", "research_report.schema.json"
            )
            validator = OutputSchemaValidator(schema_path)
            valid_json_dict = await validator.validate_and_fix(cleaned_content, max_retries=2, timeout_sec=8.0)
            
            # Phase 5 Confidence Estimator Overwrite
            naive_conf = valid_json_dict.get("confidence", 0.75)
            structured_conf = estimate_report_confidence(valid_json_dict)
            
            # Subtly backup naive AI guess into structured meta
            if "metadata" not in valid_json_dict:
                valid_json_dict["metadata"] = {}
            valid_json_dict["metadata"]["model_confidence"] = naive_conf
            
            # Force replace outbound struct
            valid_json_dict["confidence"] = structured_conf
            
            # Phase 4 Claim Extraction Graph Hook
            # 1. Structure Database Persistence
            metadata = valid_json_dict.get("metadata", {})
            report = GeneratedReport(
                query=state.get("question", ""),
                structured_content=valid_json_dict,
                confidence=structured_conf,
                model_used=metadata.get("model", ""),
                tokens_used=metadata.get("tokens_used", 0),
                latency_ms=metadata.get("latency", 0),
                schema_version=valid_json_dict.get("version", "1.0"),
                confidence_version=DEFAULT_CONFIDENCE_VERSION,
                generation_status="completed"
            )
            await report.save()
            
            # 2. Check Feature Toggle and trigger background claims worker
            if os.getenv("SYNAPSE_ENABLE_CLAIM_INGESTION", "true").lower() == "true":
                submit_command("open_notebook", "extract_claims", {"report_id": str(report.id)})
                logger.info(f"Enqueued extract_claims job for report {report.id}")
            else:
                logger.info("claim_ingestion_skipped_reason: SYNAPSE_ENABLE_CLAIM_INGESTION feature toggle is disabled")

            # Serialize back to string for the pipeline state (or return dict depending on state definition)
            # `ThreadState.final_answer` expects a string
            cleaned_content = json.dumps(valid_json_dict, indent=2)

        return {"final_answer": cleaned_content}
    except OpenNotebookError:
        raise
    except Exception as e:
        error_class, user_message = classify_error(e)
        raise error_class(user_message) from e


agent_state = StateGraph(ThreadState)
agent_state.add_node("agent", call_model_with_messages)
agent_state.add_node("provide_answer", provide_answer)
agent_state.add_node("write_final_answer", write_final_answer)
agent_state.add_edge(START, "agent")
agent_state.add_conditional_edges("agent", trigger_queries, ["provide_answer"])
agent_state.add_edge("provide_answer", "write_final_answer")
agent_state.add_edge("write_final_answer", END)

graph = agent_state.compile()

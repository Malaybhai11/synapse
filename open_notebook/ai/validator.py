import asyncio
import json
import os
import re
import time
from typing import Any, Dict

import jsonschema
from loguru import logger

from open_notebook.ai.provision import provision_langchain_model
from open_notebook.exceptions import SchemaValidationError
from open_notebook.utils.text_utils import extract_text_content


class OutputSchemaValidator:
    """
    Validates LLM raw output against a JSON Schema.
    Features:
      - Regex JSON block extraction
      - jsonschema Draft7 Validation (Strict 'additionalProperties': False)
      - Self-healing retries via a deterministic LLM fixer
      - Timeout protections
      - Structured deterministic error objects
      - Performance metrics recording
    """

    def __init__(self, schema_path: str):
        self.schema_path = schema_path
        self._schema = self._load_schema()
        # Initialize internal validator using Draft7 specification
        jsonschema.Draft7Validator.check_schema(self._schema)
        self.validator = jsonschema.Draft7Validator(self._schema)

    def _load_schema(self) -> Dict[str, Any]:
        """Loads JSON schema from the filesystem."""
        try:
            with open(self.schema_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load schema from {self.schema_path}: {e}")
            raise RuntimeError(f"Could not initialize validator for {self.schema_path}") from e

    def _extract_json_block(self, raw: str) -> str:
        """
        Extracts the first logical JSON block from conversational wrappers.
        Helps prevent validation failures when LLM prepend answers with 'Here is your report:\\n'
        """
        # Strip potential markdown code blocks first
        raw_cleaned = raw.strip()
        if raw_cleaned.startswith("```json"):
            raw_cleaned = raw_cleaned[7:]
        elif raw_cleaned.startswith("```"):
            raw_cleaned = raw_cleaned[3:]
        if raw_cleaned.endswith("```"):
            raw_cleaned = raw_cleaned[:-3]
        
        raw_cleaned = raw_cleaned.strip()

        # Attempt immediate parsing in case it's perfectly clean
        try:
            json.loads(raw_cleaned)
            return raw_cleaned
        except json.JSONDecodeError:
            pass
        
        # Incremental search for root JSON object {}
        first_brace = raw_cleaned.find('{')
        last_brace = raw_cleaned.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            extracted = raw_cleaned[first_brace:last_brace+1]
            try:
                json.loads(extracted)
                return extracted
            except json.JSONDecodeError:
                pass # Extracted block wasn't valid, rely on LLM schema_fix

        raise ValueError("No valid extracting JSON object found in response.")

    def _get_validation_errors(self, instance: Any) -> list[str]:
        """Runs the validation and formats all jsonschema errors."""
        errors = []
        for error in self.validator.iter_errors(instance):
            path = " -> ".join([str(p) for p in error.path]) if error.path else "root"
            errors.append(f"Field '{path}': {error.message}")
        return errors

    async def _schema_fix(self, raw_input: str, validation_errors: list[str]) -> str:
        """
        Uses a separate LLM call to fix the schema structure deterministically.
        Uses a low-temperature model instance to avoid creative hallucination.
        """
        prompt = f"""You are a rigid structural formatting tool.
Your job is to repair a broken JSON payload so that it perfectly aligns with the provided JSON Schema.

CRITICAL INSTRUCTIONS:
1. Return ONLY the completely valid JSON data structure.
2. DO NOT output any conversational text, pleasantries, explanations, or markdown code blocks (like ```json).
3. Ensure absolute compliance with the schema rules (e.g., additionalProperties is strictly FALSE, you MUST remove fields not defined in the schema).
4. Do NOT hallucinate or add any new data fields that were not in the original payload, except when filling required properties with neutral defaults (e.g., empty arrays or "Not provided" strings).

== TARGET JSON SCHEMA ==
{json.dumps(self._schema, indent=2)}

== ORIGINAL PAYLOAD ==
{raw_input}

== VALIDATION ERRORS ==
{json.dumps(validation_errors, indent=2)}

OUTPUT THE CORRECTED JSON PAYLOAD NOW:
"""
        # Utilize a fast, cheap, predictable configuration suitable for strict text fixes
        # e.g. gpt-4o-mini, defaulting to 'language' type, using temperature=0 if supported by provider settings
        model = await provision_langchain_model(
            content=prompt,
            model_id=None,
            default_type="language",
            temperature=0  # Requesting zero temperature for determinism
        )
        
        result = await model.ainvoke(prompt)
        return extract_text_content(result.content)

    async def _execute_with_timeout(self, raw_response: str, max_retries: int) -> Dict[str, Any]:
        """Internal execution tracking multiple retries without global timeout"""
        current_input = raw_response
        retries_used = 0

        logger.bind(metrics=True).info(
            "OutputSchemaValidator invoked",
            validator_invocations=1
        )

        while retries_used <= max_retries:
            extraction_failed = False
            parsed_json = None
            validation_errors = []

            # Step 1: Extract block
            try:
                extracted_json_str = self._extract_json_block(current_input)
            except ValueError as e:
                extraction_failed = True
                validation_errors = [str(e)]
                extracted_json_str = current_input

            # Step 2: Parse
            if not extraction_failed:
                try:
                    parsed_json = json.loads(extracted_json_str)
                except json.JSONDecodeError as e:
                    extraction_failed = True
                    validation_errors = [f"JSON Parse Error: {e.msg} at line {e.lineno}"]

            # Step 3: Validate logic
            if not extraction_failed and parsed_json is not None:
                validation_errors = self._get_validation_errors(parsed_json)

            # Check if perfectly clear
            if not validation_errors and parsed_json is not None:
                if retries_used > 0:
                    logger.bind(metrics=True).info(
                        "Schema fixed successfully",
                        fixer_success=1,
                        retries=retries_used
                    )
                return parsed_json

            # Proceed to Schema Fixer if retries available
            if retries_used < max_retries:
                logger.warning(f"Schema validation failed. Attempting fixer. Errors: {validation_errors}")
                logger.bind(metrics=True).info("Schema fixer invoked", fixer_invocations=1)
                
                # Use schema fixer
                try:
                    current_input = await self._schema_fix(current_input, validation_errors)
                    retries_used += 1
                except Exception as e:
                    logger.error(f"Schema fixer internal failure: {e}")
                    # If fixer itself crashes, jump out early to avoid infinite loop of fails
                    break
            else:
                # Exhausted
                break

        # If loop finishes without returning, validation persistently failed
        logger.bind(metrics=True).error(
            "Schema fix failed permanently",
            fixer_fail=1,
            final_retries=retries_used
        )
        excerpt = current_input[:500] + ("..." if len(current_input) > 500 else "")
        raise SchemaValidationError(
            message="LLM generated structure strictly violates REQUIRED output schema.",
            errors=validation_errors,
            retries_used=retries_used,
            raw_output_excerpt=excerpt
        )

    async def validate_and_fix(self, raw_response: str, max_retries: int = 2, timeout_sec: float = 8.0) -> Dict[str, Any]:
        """
        Public facing method.
        Wraps the validation/fixing logic in an aggressive asyncio timeout circuit breaker.
        """
        start_time = time.perf_counter()
        try:
            result = await asyncio.wait_for(
                self._execute_with_timeout(raw_response, max_retries),
                timeout=timeout_sec
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            logger.bind(metrics=True).info(
                "OutputSchemaValidator finished", 
                schema_validation_latency_ms=elapsed_ms
            )
            return result
        except asyncio.TimeoutError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.bind(metrics=True).error(
                "OutputSchemaValidator timeout circuit breaker triggered.",
                schema_validation_latency_ms=elapsed_ms
            )
            raise SchemaValidationError(
                message=f"Schema validation and fixing timed out after {timeout_sec}s",
                errors=["asyncio.TimeoutError"],
                retries_used=-1,
                raw_output_excerpt=raw_response[:500]
            ) from e

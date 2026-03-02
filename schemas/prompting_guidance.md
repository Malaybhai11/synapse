# LLM Prompting Guidance for Synapse Schemas

To produce output matching the `ResearchReport` schema (which includes the `Claim` schema), you can use function calling (tool use) or an instruction-based JSON mode pattern depending on your LLM API.

## Pattern 1: Function Calling / Tool Use (Recommended)

When using modern models (like OpenAI GPT-4, Anthropic Claude 3.5 Sonnet, Gemini 1.5 Pro) that support native tool use or structured outputs:

1. Define a tool/function named `generate_research_report`.
2. Pass the structure of `research_report.schema.json` as the `parameters` definition.
3. Provide the user's topic and tell the model to call this function to report its findings.

**Example Prompt Fragment:**
> You are an expert AI research assistant for the Synapse application. You must perform deep research on the query provided below. Once you have gathered sufficient evidence and analysis, synthesize your findings by calling the `generate_research_report` tool with your structured response. Every claim must have a linked source_id. Ensure your confidence score reflects your certainty.

## Pattern 2: JSON Mode / Instruction Pattern

For models that support JSON Mode (e.g. OpenAI with `response_format: { "type": "json_object" }` or when prompting open-weights models):

**Example Prompt Fragment:**
> You are an expert AI research assistant. Provide an in-depth analysis of the user's query.
>
> You MUST return your final response strictly as a JSON object adhering to the following JSON Schema:
> ```json
> {
>   "type": "object",
>   "properties": {
>     "id": { "type": "string" },
>     "query": { "type": "string" },
>     ...
>   }
> }
> ```
> Do not include any text, markdown formatting (like ```json), or explanations outside of the raw JSON object. Ensure all required fields, including the `claims` array, are populated correctly.

## Key Considerations for the Prompt:
- **No Additional Properties**: Clearly state that `additionalProperties: false` is in effect; thus the model must never hallucinate extra fields outside the schema.
- **Claim Structure**: Emphasize extraction of discrete claims with `polarity` (supports/opposes/neutral) and RDF-like `subject`/`predicate`/`object` triplets for automated reasoning.
- **Latency & Metadata**: Instruct the model that final performance metadata must include `latency_ms` and a matching `version` (currently 1.1.0).
- **Array Size Enforcements**: Mention that at least one item must exist in `sources`, `claims`, and `technical_breakdown` arrays (minItems: 1).

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
- **Stringent Typing**: Warn the LLM that boolean or null values are not accepted in string-only fields (e.g., comparison table rows).
- **Source Indexing**: Require the LLM to provide valid URIs and matching `source_id`/`doc_id` inside the `claims` and `sources` arrays.
- **DateTime Format**: Specify that `timestamp` must rigidly be in ISO 8601 format.

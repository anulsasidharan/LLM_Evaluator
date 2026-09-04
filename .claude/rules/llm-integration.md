# LLM Integration Rules

## Tool Calling
- All LLM tool functions must have clear Pydantic input/output schemas
- Tools must be idempotent — safe to retry on failure
- Always set a timeout on LLM API calls (60s default)
- Log every tool call and result for debugging

## Multi-Provider Fallback
- Primary: Anthropic Claude
- Secondary: OpenAI GPT-4
- Tertiary: Google Gemini
- On provider failure, retry once, then fall back to next provider
- Log which provider served each request

## Prompt Engineering
- System prompts live in `backend/app/prompts/` as plain text files
- Never hardcode prompts in service code
- Include structured output instructions in prompts
- Keep tool descriptions concise but unambiguous

## Cost Control
- Cache LLM responses keyed on (model_name, depth, tool_results_hash)
- Use the cheapest model that meets quality requirements for each sub-task
- Track token usage per request in the database

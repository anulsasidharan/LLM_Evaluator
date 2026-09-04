---
name: llm-analysis
description: >-
  Orchestrate multi-tool LLM analysis of a model: gather benchmarks, specs,
  capabilities, and resource requirements, then synthesize into a structured
  report. Use when the user asks to analyze, evaluate, or profile an LLM model.
---

# LLM Analysis Skill

## Workflow

1. **Identify the model** — resolve the canonical name and vendor
2. **Gather data** — call tools in parallel:
   - `search_benchmarks` for performance scores
   - `fetch_model_specs` for technical details
   - `analyze_capabilities` for strengths/weaknesses
   - `calculate_resource_requirements` for hosting needs
   - `find_competitors` for alternatives
3. **Normalize** — convert all scores to 0–100 scale, unify naming
4. **Synthesize** — produce a report following the template in CLAUDE.md §8.1
5. **Validate** — ensure all required sections are populated

## Output Format

Return a JSON object matching the `ModelProfile` + `BenchmarkResult[]` + `ResourceRequirement` schemas from CLAUDE.md §4.

## Error Handling

- If a data source is unavailable, note it in the report and proceed with available data
- Never fabricate benchmark scores — mark missing data as `null` with a reason

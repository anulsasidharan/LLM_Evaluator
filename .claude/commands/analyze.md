# /project:analyze

Analyze an LLM model end-to-end. Given a model name:

1. Search for the model across HuggingFace, official sources, and papers
2. Gather benchmark scores (MMLU, ARC, HellaSwag, TruthfulQA, etc.)
3. Extract technical specs (parameters, context window, architecture, precision)
4. Identify capabilities, strengths, and known limitations
5. Calculate resource requirements for local hosting (minimum, optimal, maximum)
6. Find competing models in the same category
7. Generate a structured report following the template in CLAUDE.md §8.1

Usage: `/project:analyze <model_name>`

Output: A full ModelProfile + report in the format defined by the Report Structure.

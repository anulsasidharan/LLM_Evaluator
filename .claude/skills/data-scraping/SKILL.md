---
name: data-scraping
description: >-
  Scrape and normalize LLM benchmark data from HuggingFace, official model
  pages, ArXiv, and vendor sites. Use when implementing or debugging the data
  collection pipeline, adding new data sources, or troubleshooting scraping
  failures.
---

# Data Scraping Skill

## Supported Sources

| Source | Method | Key Data |
|--------|--------|----------|
| HuggingFace Hub | REST API | Model cards, configs, scores |
| Official model pages | Web scraping (Playwright) | Benchmarks, specs |
| ArXiv | REST API | Papers, architecture details |
| Ollama Registry | REST API | Local hosting compatibility |
| VLLM docs | Web scraping | Inference optimization specs |

## Implementation Guidelines

- Store raw responses before normalization
- Tag every record with `source`, `source_url`, `scraped_at`
- Respect rate limits: add delays between requests, honor `robots.txt`
- Use exponential backoff (base 2s, max 60s) on transient HTTP errors
- Normalize benchmark names to canonical forms (see `rules/data-pipeline.md`)

## Adding a New Source

1. Create a new integration file in `backend/app/integrations/`
2. Implement the `DataSourceInterface` (fetch, parse, normalize)
3. Register in the source registry
4. Add corresponding tests with mocked HTTP responses

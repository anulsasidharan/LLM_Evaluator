# Data Pipeline Rules

## Scraping
- Respect `robots.txt` and rate limits on all external sources
- Use exponential backoff on transient failures
- Store raw scraped data before normalization (audit trail)
- Add a `source` and `scraped_at` timestamp to every record

## Normalization
- All benchmark scores normalized to 0–100 scale
- Standardized benchmark names (e.g. "MMLU", not "mmlu" or "Massive Multitask")
- Model parameter counts stored as integers (not "70B" strings)
- Dates stored as ISO 8601 UTC

## Caching
- Model profiles: 7-day TTL in Redis
- Benchmark results: 3-day TTL
- Comparison reports: 1-day TTL
- LLM analysis results: 1-day TTL keyed on query hash
- Always serve stale cache on upstream failure (stale-while-revalidate)

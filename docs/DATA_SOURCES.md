# Data Sources

| Source | Module | Status |
|--------|--------|--------|
| HuggingFace Hub | `backend/app/integrations/huggingface.py` | Scaffold |
| ArXiv | `backend/app/integrations/arxiv.py` | Scaffold |
| Ollama | `backend/app/integrations/ollama.py` | Scaffold |
| Vendor pages | `backend/app/integrations/external_sources.py` | Scaffold |
| vLLM docs | `backend/app/integrations/external_sources.py` | Scaffold |

Every source must implement `DataSourceInterface` (`fetch`, `parse`, `normalize`) and stamp `source`, `source_url`, and `scraped_at` on records. Benchmark scores are normalized to a 0–100 scale.

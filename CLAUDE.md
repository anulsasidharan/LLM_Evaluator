# LLM Model Evaluator - CLAUDE.md

**Project**: LLM Model Evaluator for Uniball  
**Version**: 1.0  
**Last Updated**: 2026-09-03  
**Status**: Planning & Architecture Phase

---

## 1. Project Overview

### Vision
The LLM Model Evaluator is a comprehensive analytical platform that enables users to understand, compare, and evaluate Large Language Models (LLMs) through automated benchmarking, capability analysis, and resource requirement assessment.

### Core Problem Statement
Users need a centralized, data-driven solution to:
- Assess LLM capabilities and limitations
- Compare models across multiple dimensions
- Understand resource requirements for deployment
- Make informed decisions about model selection
- Generate shareable, visual reports for stakeholders

### Key Value Propositions
1. **Automated Analysis**: Intelligent scraping and analysis of benchmarks from official sources
2. **Holistic Comparison**: Side-by-side capability and performance trade-off analysis
3. **Deployment Insights**: Local hosting feasibility and resource requirements (min/optimal/max)
4. **Visual Reports**: Professional, easy-to-understand graphical analysis
5. **Extensibility**: Multiple LLM backends (OpenAI, Anthropic, Google, etc.) for analysis

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (Web UI)                        │
│  - Model Search & Query Interface                            │
│  - Interactive Report Dashboard                              │
│  - Comparison Visualizations                                 │
│  - Export Functionality                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST/GraphQL API
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (API Server)                      │
│  - Request Routing & Validation                              │
│  - Cache Management                                          │
│  - Report Generation Orchestration                           │
│  - Data Aggregation & Normalization                          │
│  - User Management & Authentication                          │
└────┬──────────────┬──────────────────┬─────────────────────┘
     │              │                  │
     ▼              ▼                  ▼
┌─────────────┐ ┌──────────────┐ ┌────────────────┐
│ Data Layer  │ │ Cache Layer  │ │ LLM Analysis   │
│ - PostgreSQL│ │ - Redis      │ │ Layer          │
│ - Document │ │              │ │ (Tool Calling) │
│   Storage  │ │              │ │                │
└─────────────┘ └──────────────┘ └────────────────┘
     ▲              ▲                  ▲
     └──────────────┼──────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
   ┌──────────────┐      ┌──────────────┐
   │Data Sources  │      │LLM Backends  │
   │- HuggingFace│      │- Anthropic   │
   │- VLLM       │      │- OpenAI      │
   │- Ollama     │      │- Google      │
   │- Papers     │      │- Meta        │
   └──────────────┘      └──────────────┘
```

---

## 3. Component Breakdown

### 3.1 Frontend Layer
**Technology Stack**: React/Next.js, TypeScript, TailwindCSS, Recharts/D3.js

**Key Components**:
- `ModelSearchPanel`: Input field to search/query model names
- `ReportDashboard`: Main display for generated reports
- `ComparisonMatrix`: Side-by-side model comparison view
- `ResourceChart`: Visualization of hosting requirements
- `CapabilityTable`: Detailed capability matrix
- `ExportPanel`: PDF/JSON export options

**User Workflows**:
1. User enters model name
2. System fetches or generates report
3. Dashboard displays with interactive visualizations
4. User can compare with other models
5. User exports report

### 3.2 Backend Layer
**Technology Stack**: Python (FastAPI/Django) or Node.js (Express), TypeScript

**Key Modules**:

#### A. API Server
- RESTful endpoints for model queries
- Real-time report generation with polling
- Webhook support for long-running analyses
- Authentication & rate limiting
- Request validation & error handling

#### B. Data Aggregation Service
- Multi-source data collection:
  - **HuggingFace Hub**: Model cards, benchmark scores
  - **Ollama**: Local hosting compatibility
  - **VLLM**: Inference optimization specs
  - **ArXiv/Papers**: Research papers on architecture
  - **Official vendor sites**: Benchmark claims (OpenAI, Anthropic, Google)
- Normalization layer to standardize metrics
- Caching of scraped data

#### C. Analysis Engine
- Comparative analysis logic
- Resource calculation based on:
  - Model size (parameters)
  - Precision (FP32, FP16, INT8, etc.)
  - Batch size requirements
  - Hardware compatibility
- Trade-off analysis generation

#### D. Report Generation Service
- Template-based report creation
- Chart & visualization generation
- Multi-format output (JSON, PDF, HTML)
- Async processing with job queue

### 3.3 LLM Layer (AI Analysis & Tool-Calling)
**Supported LLM Backends**:
- Anthropic Claude (primary)
- OpenAI GPT-4
- Google Gemini
- Fallback mechanism for redundancy

**Tool-Calling Capabilities**:

#### Tools Available to LLM:
1. `search_benchmarks(model_name, benchmark_type)` → Fetch official benchmarks
2. `fetch_model_specs(model_name)` → Get technical specifications
3. `analyze_capabilities(model_name)` → Extract capability claims
4. `find_competitors(model_name, category)` → Identify comparable models
5. `calculate_resource_requirements(model_name, deployment_type)` → Compute hosting needs
6. `generate_trade_off_analysis(model1, model2)` → Compare two models
7. `fetch_research_papers(model_name, topic)` → Get academic references
8. `extract_performance_metrics(model_name)` → Parse and normalize scores

**LLM Workflow**:
```
User Query (Model Name)
    ↓
LLM receives query with tools
    ↓
LLM decides which tools to call
    ↓
Backend executes tool calls in parallel
    ↓
LLM synthesizes results into report
    ↓
Report enriched with visualizations
    ↓
Return to frontend
```

---

## 4. Data Model

### 4.1 Core Entities

#### ModelProfile
```json
{
  "id": "uuid",
  "name": "gpt-4-turbo",
  "vendor": "OpenAI",
  "version": "2024-04-09",
  "parameters": 1000000000,
  "releaseDate": "2024-04-09",
  "description": "...",
  "officialUrl": "https://...",
  "tags": ["LLM", "Multimodal", "Instruction-tuned"],
  "specs": {
    "contextWindow": 128000,
    "trainingDataCutoff": "2023-12",
    "architecture": "Transformer",
    "precision": ["FP32", "FP16", "INT8"]
  },
  "benchmarks": {}, // Aggregated
  "capabilities": {}, // Structured capability matrix
  "flaws": [], // Known limitations
  "updatedAt": "2026-09-03T12:00:00Z"
}
```

#### BenchmarkResult
```json
{
  "id": "uuid",
  "modelId": "uuid",
  "benchmarkName": "MMLU",
  "score": 86.4,
  "percentile": 95,
  "source": "official|huggingface|papers",
  "sourceUrl": "https://...",
  "metadata": {
    "evaluationDate": "2024-08",
    "sampleSize": 14042
  },
  "recordedAt": "2026-09-03T12:00:00Z"
}
```

#### ResourceRequirement
```json
{
  "id": "uuid",
  "modelId": "uuid",
  "deploymentType": "local|cloud|edge",
  "hostingOption": "ollama|vllm|llama.cpp",
  "requirements": {
    "minimum": {
      "gpuMemory": "16GB",
      "cpuCores": 8,
      "ramGb": 32,
      "storageSsd": "100GB",
      "inferenceTime": "2s/token"
    },
    "optimal": {
      "gpuMemory": "40GB",
      "cpuCores": 16,
      "ramGb": 64,
      "storageSsd": "200GB",
      "inferenceTime": "0.1s/token"
    },
    "maximum": {
      "gpuMemory": "80GB",
      "cpuCores": 32,
      "ramGb": 128,
      "storageSsd": "500GB",
      "inferenceTime": "0.01s/token"
    }
  }
}
```

#### ComparisonReport
```json
{
  "id": "uuid",
  "userId": "uuid",
  "modelsCompared": ["uuid1", "uuid2"],
  "generatedAt": "2026-09-03T12:00:00Z",
  "expiresAt": "2026-10-03T12:00:00Z",
  "reportData": {
    "summary": "...",
    "capabilityMatrix": {},
    "benchmarkComparison": {},
    "resourceComparison": {},
    "recommendations": [],
    "tradeOffs": []
  },
  "exportFormats": ["pdf", "json", "html"]
}
```

---

## 5. Data Sources & Integration

### 5.1 External Data Sources

| Source | Type | Update Frequency | Key Data |
|--------|------|------------------|----------|
| HuggingFace Hub | API | Real-time | Model cards, scores, configs |
| Official Model Pages | Web Scraping | Weekly | Benchmarks, specs, capabilities |
| ArXiv/Papers | Web Scraping | Daily | Research, architecture, results |
| Ollama Registry | API | Real-time | Local hosting specs |
| VLLM Docs | Web Scraping | Weekly | Optimization guidelines |
| Industry Reports | Manual | Monthly | Market analysis |

### 5.2 Data Collection Pipeline

```
Scheduled Jobs (Daily/Weekly)
    ↓
├─ Scrape HuggingFace Hub
├─ Fetch official benchmarks
├─ Search ArXiv for new papers
├─ Update Ollama specs
└─ Normalize & enrich data
    ↓
Store in PostgreSQL
    ↓
Cache in Redis
    ↓
Available for LLM tool calls
```

---

## 6. API Specification

### 6.1 REST Endpoints

#### `POST /api/v1/models/analyze`
**Purpose**: Initiate model analysis
```json
Request:
{
  "modelName": "claude-3-opus",
  "depth": "quick|standard|detailed",
  "compareWith": ["gpt-4-turbo", "gemini-pro"], // Optional
  "includeResources": true,
  "exportFormat": "json|pdf|html"
}

Response:
{
  "jobId": "uuid",
  "status": "queued|processing|completed|failed",
  "estimatedTimeSeconds": 30,
  "resultsUrl": "/api/v1/results/{jobId}"
}
```

#### `GET /api/v1/results/{jobId}`
**Purpose**: Retrieve analysis results
```json
Response:
{
  "jobId": "uuid",
  "status": "completed",
  "completedAt": "2026-09-03T12:30:00Z",
  "report": {
    "model": { /* ModelProfile */ },
    "benchmarks": [ /* Array */ ],
    "capabilities": { /* Matrix */ },
    "flaws": [ /* Array */ ],
    "competitors": [ /* Array */ ],
    "resources": { /* ResourceRequirement */ },
    "analysis": "...", // LLM-generated synthesis
    "recommendations": []
  }
}
```

#### `GET /api/v1/models/search?q={query}`
**Purpose**: Search models by name or tag
```json
Response:
{
  "results": [
    {
      "id": "uuid",
      "name": "claude-3-opus",
      "vendor": "Anthropic",
      "parameters": 1000000000,
      "releaseDate": "2024-08",
      "tags": ["LLM", "Multimodal"]
    }
  ],
  "total": 150
}
```

#### `POST /api/v1/comparisons`
**Purpose**: Compare multiple models
```json
Request:
{
  "modelIds": ["uuid1", "uuid2", "uuid3"],
  "focusAreas": ["capabilities", "speed", "cost", "resources"]
}

Response:
{
  "comparisonId": "uuid",
  "comparison": {
    "models": [],
    "matrix": { /* Structured comparison */ },
    "bestFor": { /* Use-case recommendations */ },
    "tradeOffs": [ /* Key differences */ ]
  }
}
```

---

## 7. LLM Integration Strategy

### 7.1 Prompt Framework

**System Prompt** (for Claude/GPT-4):
```
You are an expert AI/ML analyst specializing in Large Language Model evaluation.
Your task is to analyze LLM capabilities, limitations, and deployment considerations.

When given a model name:
1. Use the search_benchmarks tool to gather official performance data
2. Use fetch_model_specs to get technical details
3. Use analyze_capabilities to identify strengths
4. Use find_competitors to identify alternative models
5. Use calculate_resource_requirements for deployment scenarios
6. Use generate_trade_off_analysis to compare options

Synthesize findings into a comprehensive, accessible report highlighting:
- Key strengths and ideal use cases
- Known limitations and failure modes
- Resource requirements for different deployment scenarios
- Comparison with competing models
- Specific recommendations for different user profiles
```

### 7.2 Tool-Calling Flow

```python
class LLMAnalyzer:
    def analyze_model(self, model_name: str):
        """
        Multi-turn LLM interaction with tool calling
        """
        messages = [
            {"role": "user", "content": f"Analyze the {model_name} LLM comprehensively"}
        ]
        
        while True:
            response = llm.call(
                messages=messages,
                tools=get_available_tools(),
                model="claude-3-opus"  # Primary
            )
            
            if response.stop_reason == "tool_use":
                # Execute tools
                tool_results = execute_tools(response.tool_calls)
                
                # Continue conversation
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            
            else:  # stop_reason == "end_turn"
                return synthesize_report(response.content)
```

---

## 8. Report Generation

### 8.1 Report Structure

```
LLM Model Evaluator Report
══════════════════════════

Executive Summary
├─ Model: [Name]
├─ Vendor: [Vendor]
├─ Overall Rating: [Score/10]
└─ Best Use Cases: [List]

1. Model Overview
├─ Release Date
├─ Parameters
├─ Context Window
├─ Training Data Cutoff
└─ Architecture Details

2. Capability Analysis
├─ Strengths (with benchmarks)
├─ Weaknesses/Flaws
├─ Ideal Use Cases
└─ Poor Use Cases

3. Performance Benchmarks
├─ MMLU
├─ ARC
├─ HellaSwag
├─ TruthfulQA
├─ [Other relevant benchmarks]
└─ Comparison vs competitors

4. Deployment Options
├─ Cloud Deployment
│  ├─ Available Providers
│  ├─ Cost Estimates
│  └─ Performance Characteristics
├─ Local Hosting (if viable)
│  ├─ Minimum Requirements
│  ├─ Optimal Setup
│  ├─ Maximum Performance
│  └─ Quantization Options
└─ API Access

5. Trade-Off Analysis
├─ vs Competitor A
├─ vs Competitor B
├─ vs Competitor C
└─ When to Choose This Model

6. Resource Requirements Matrix
├─ Minimum Viable
├─ Production-Ready
└─ High-Performance

7. Recommendations
└─ For different user profiles
```

### 8.2 Visualizations Included

- **Benchmark Radar Chart**: Multi-dimensional performance
- **Capability Heatmap**: Strengths across domains
- **Resource Requirement Bar Charts**: CPU/GPU/Memory needs
- **Comparison Table**: Side-by-side with competitors
- **Performance vs Cost Scatter**: Value analysis
- **Timeline**: Evolution and updates

---

## 9. Technology Stack

### Backend
- **Runtime**: Python 3.11+ or Node.js 20+
- **Framework**: FastAPI (Python) or Express.js
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Task Queue**: Celery + RabbitMQ OR Bull (Node.js)
- **LLM SDK**: Anthropic SDK (primary), OpenAI SDK, Google SDK
- **Scraping**: BeautifulSoup4, Scrapy, or Playwright
- **Async**: asyncio, aiohttp

### Frontend
- **Framework**: Next.js 14+ with TypeScript
- **Styling**: TailwindCSS
- **Charts**: Recharts or D3.js
- **API Client**: TanStack Query (React Query)
- **State Management**: Zustand or Redux
- **Export**: html2pdf, jsPDF for client-side generation

### DevOps
- **Containerization**: Docker & Docker Compose
- **Orchestration**: Kubernetes (optional for scaling)
- **CI/CD**: GitHub Actions, GitLab CI
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack or Datadog

---

## 10. Development Workflow

### Phase 1: MVP (Weeks 1-2)
- [ ] Backend API scaffold
- [ ] Single LLM backend (Anthropic Claude)
- [ ] Core tools for analysis
- [ ] Basic frontend interface
- [ ] Database schema

### Phase 2: Feature Expansion (Weeks 3-4)
- [ ] Multiple LLM backends
- [ ] Advanced comparison features
- [ ] Resource calculator refinement
- [ ] Report export (PDF, JSON)

### Phase 3: Polish & Scale (Weeks 5+)
- [ ] Performance optimization
- [ ] Caching strategy
- [ ] User authentication
- [ ] Analytics & usage tracking
- [ ] Production deployment

---

## 11. Important Files & Directory Structure

```
llm-model-evaluator/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── config.py               # Configuration
│   │   ├── models/
│   │   │   ├── schemas.py          # Pydantic schemas
│   │   │   └── database.py         # Database models
│   │   ├── api/
│   │   │   ├── routes.py           # API endpoints
│   │   │   └── tools.py            # Tool definitions
│   │   ├── services/
│   │   │   ├── llm_service.py      # LLM interactions
│   │   │   ├── data_service.py     # Data aggregation
│   │   │   ├── analysis_service.py # Analysis logic
│   │   │   └── report_service.py   # Report generation
│   │   ├── integrations/
│   │   │   ├── huggingface.py
│   │   │   ├── arxiv.py
│   │   │   ├── ollama.py
│   │   │   └── external_sources.py
│   │   └── tasks/
│   │       └── celery_tasks.py     # Background jobs
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Main search page
│   │   │   ├── results/page.tsx    # Results dashboard
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── ModelSearch.tsx
│   │   │   ├── ReportDashboard.tsx
│   │   │   ├── ComparisonMatrix.tsx
│   │   │   ├── ResourceChart.tsx
│   │   │   └── CapabilityTable.tsx
│   │   ├── services/
│   │   │   └── api.ts             # API client
│   │   ├── hooks/
│   │   │   └── useModelAnalysis.ts
│   │   └── types/
│   │       └── index.ts           # TypeScript types
│   ├── package.json
│   └── Dockerfile
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API_SPEC.md
│   ├── DATA_SOURCES.md
│   └── DEPLOYMENT.md
│
├── CLAUDE.md                       # This file
├── README.md
└── .github/
    └── workflows/
        ├── ci.yml
        └── deploy.yml
```

---

## 12. Key Integration Points

### LLM Backends
- **Anthropic Claude**: Primary (fastest tool support)
- **OpenAI GPT-4**: Secondary fallback
- **Google Gemini**: Tertiary option
- **Fallback Strategy**: If primary unavailable, queue for retry

### Data Sources
- HuggingFace API: Official models & benchmarks
- Ollama: Local hosting capability matrix
- Official websites: Direct benchmark claims
- ArXiv API: Research papers
- Custom web scrapers: Vendor benchmark pages

### Cache Strategy
- Cache model profiles: 7 days
- Cache benchmark results: 3 days
- Cache comparison reports: 1 day
- Cache LLM analysis: 1 day (for same query)

---

## 13. Development Guidelines

### Code Standards
- Python: PEP 8, type hints required
- TypeScript: Strict mode, interfaces over types
- Async-first approach
- Comprehensive error handling
- Logging at key points

### Testing Strategy
- Unit tests for data normalization
- Integration tests for LLM tools
- End-to-end tests for API flows
- Load testing for comparison reports

### Git Workflow
- Feature branches from `develop`
- PR reviews before merge to `develop`
- Release branches for production deployment
- Semantic versioning

---

## 14. Success Metrics

### MVP Success Criteria
- [ ] Model analysis completes in < 60 seconds
- [ ] 95%+ accuracy in benchmark scraping
- [ ] Supports ≥10 popular models
- [ ] Report generation in 3+ formats
- [ ] Supports local hosting comparison

### Scale Metrics
- [ ] Supports 1000+ models in database
- [ ] Handles 100 concurrent analysis requests
- [ ] Cache hit rate > 80%
- [ ] P95 response time < 5 seconds
- [ ] 99.9% availability

---

## 15. Next Steps

1. **Review & Refinement**: Validate architecture with team
2. **Database Design**: Finalize schema with ER diagrams
3. **API Specification**: Detailed endpoint documentation
4. **LLM Tools**: Implement and test tool definitions
5. **Frontend Wireframes**: Design report visualizations
6. **Data Pipeline**: Build initial scraping infrastructure
7. **Backend Setup**: Initialize project structure
8. **Frontend Setup**: Initialize Next.js project

---

## 16. References & Resources

- HuggingFace Hub: https://huggingface.co/
- Ollama: https://ollama.ai/
- VLLM: https://vllm.ai/
- ArXiv API: https://arxiv.org/help/api
- Anthropic API: https://docs.anthropic.com/
- OpenAI API: https://platform.openai.com/docs/

---

**Document Version**: 1.0  
**Created**: 2026-09-03  
**Next Review**: Upon completion of Phase 1

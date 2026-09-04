---
name: report-generation
description: >-
  Generate visual LLM evaluation reports in JSON, PDF, and HTML formats
  including charts and comparison matrices. Use when implementing or debugging
  report generation, export features, or visualization components.
---

# Report Generation Skill

## Report Structure

Follow the template defined in CLAUDE.md §8.1:
- Executive Summary
- Model Overview
- Capability Analysis
- Performance Benchmarks
- Deployment Options
- Trade-Off Analysis
- Resource Requirements Matrix
- Recommendations

## Visualizations

Each report should include data for:
- Benchmark radar chart (multi-dimensional performance)
- Capability heatmap (strengths across domains)
- Resource requirement bar charts (CPU/GPU/Memory)
- Comparison table (side-by-side with competitors)
- Performance vs cost scatter plot

## Export Formats

- **JSON**: Raw structured data matching the `ComparisonReport` schema
- **HTML**: Rendered with Recharts/D3 visualizations
- **PDF**: Generated via html2pdf from the HTML version

## Guidelines

- Never include raw API responses in reports — always normalize first
- Mark data freshness: show when each benchmark was last verified
- Include source URLs for all benchmark claims

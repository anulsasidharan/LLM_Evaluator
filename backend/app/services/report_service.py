"""Report generation for JSON, HTML, and PDF-friendly HTML."""

from __future__ import annotations

import html
import json
from typing import Any

import structlog

from app.models.schemas import AnalysisReport, ExportFormat

logger = structlog.get_logger(__name__)


class ReportService:
    """Renders an analysis report into one of the supported export formats."""

    async def export(
        self,
        report: AnalysisReport,
        fmt: ExportFormat,
    ) -> dict[str, Any] | str | bytes:
        """Serialize a report.

        JSON returns a dict. HTML returns a string. PDF returns HTML bytes suitable
        for browser print-to-PDF until a dedicated PDF engine is added.
        """
        logger.info("report_export", format=fmt.value)
        if fmt == ExportFormat.JSON:
            return report.model_dump(mode="json", by_alias=True)
        if fmt in {ExportFormat.HTML, ExportFormat.PDF}:
            rendered = self.render_html(report)
            return rendered.encode("utf-8") if fmt == ExportFormat.PDF else rendered
        raise NotImplementedError(f"Export format '{fmt.value}' is not implemented.")

    def render_html(self, report: AnalysisReport) -> str:
        """Render a self-contained HTML report."""
        model = report.model
        name = html.escape(model.name if model else "Unknown")
        vendor = html.escape(model.vendor if model else "Unknown")
        analysis = html.escape(report.analysis).replace("\n", "<br/>")
        recommendations = "".join(f"<li>{html.escape(r)}</li>" for r in report.recommendations)
        flaws = "".join(f"<li>{html.escape(f)}</li>" for f in report.flaws)
        competitors = "".join(f"<li>{html.escape(c)}</li>" for c in report.competitors)
        benchmarks = "".join(
            "<tr>"
            f"<td>{html.escape(b.benchmark_name)}</td>"
            f"<td>{'' if b.score is None else b.score}</td>"
            f"<td>{html.escape(b.source)}</td>"
            "</tr>"
            for b in report.benchmarks
        )
        resources = ""
        if report.resources:
            req = report.resources.requirements
            resources = f"""
            <h2>Resources ({html.escape(report.resources.deployment_type.value)})</h2>
            <ul>
              <li>Minimum GPU: {html.escape(req.minimum.gpu_memory or 'n/a')}</li>
              <li>Optimal GPU: {html.escape(req.optimal.gpu_memory or 'n/a')}</li>
              <li>Maximum GPU: {html.escape(req.maximum.gpu_memory or 'n/a')}</li>
            </ul>
            """
        payload = html.escape(json.dumps(report.model_dump(mode="json", by_alias=True), indent=2))
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>LLM Evaluation — {name}</title>
  <style>
    body {{ font-family: Georgia, serif; margin: 2rem; color: #18181b; background: #fafafa; }}
    h1 {{ color: #0f766e; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #d4d4d8; padding: 0.5rem; text-align: left; }}
    th {{ background: #ecfdf5; }}
    .card {{ background: white; padding: 1.25rem; border: 1px solid #e4e4e7; margin-bottom: 1rem; }}
  </style>
</head>
<body>
  <div class="card">
    <p>{vendor}</p>
    <h1>{name}</h1>
    <p>{analysis}</p>
  </div>
  <div class="card">
    <h2>Benchmarks</h2>
    <table>
      <thead><tr><th>Benchmark</th><th>Score</th><th>Source</th></tr></thead>
      <tbody>{benchmarks or '<tr><td colspan="3">No scores available</td></tr>'}</tbody>
    </table>
  </div>
  <div class="card">
    <h2>Known limitations</h2>
    <ul>{flaws or '<li>None listed</li>'}</ul>
    <h2>Competitors</h2>
    <ul>{competitors or '<li>None listed</li>'}</ul>
    <h2>Recommendations</h2>
    <ul>{recommendations or '<li>None listed</li>'}</ul>
    {resources}
  </div>
  <details class="card"><summary>Raw JSON</summary><pre>{payload}</pre></details>
</body>
</html>"""

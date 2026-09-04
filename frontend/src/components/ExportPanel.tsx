"use client";

import type { AnalysisReport } from "@/types";

interface ExportPanelProps {
  report: AnalysisReport;
  jobId?: string;
}

export function ExportPanel({ report, jobId }: ExportPanelProps) {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8002";

  function downloadJson() {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${report.model?.name ?? "report"}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function openServerExport(format: "json" | "html") {
    if (!jobId) {
      return;
    }
    window.open(`${apiBase}/api/v1/results/${jobId}/export?format=${format}`, "_blank");
  }

  return (
    <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Export</h2>
      <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
        Download the structured report or open the HTML export.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={downloadJson}
          className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm text-zinc-800 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
        >
          JSON
        </button>
        <button
          type="button"
          onClick={() => openServerExport("html")}
          disabled={!jobId}
          className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm text-zinc-800 hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
        >
          HTML
        </button>
        <button
          type="button"
          onClick={() => openServerExport("json")}
          disabled={!jobId}
          className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm text-zinc-800 hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
        >
          Server JSON
        </button>
      </div>
    </section>
  );
}

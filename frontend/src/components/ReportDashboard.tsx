"use client";

import type { AnalysisReport } from "@/types";

import { CapabilityTable } from "@/components/CapabilityTable";
import { ComparisonMatrix } from "@/components/ComparisonMatrix";
import { ExportPanel } from "@/components/ExportPanel";
import { ResourceChart } from "@/components/ResourceChart";

interface ReportDashboardProps {
  report: AnalysisReport;
  jobId?: string;
}

export function ReportDashboard({ report, jobId }: ReportDashboardProps) {
  const modelName = report.model?.name ?? "Unknown model";
  const vendor = report.model?.vendor ?? "Unknown vendor";
  const parameters = report.model?.parameters;
  const contextWindow = report.model?.specs?.contextWindow;

  return (
    <div className="flex w-full max-w-4xl flex-col gap-6">
      <header className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <p className="text-sm uppercase tracking-wide text-teal-700 dark:text-teal-400">{vendor}</p>
        <h1 className="mt-1 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">{modelName}</h1>
        <div className="mt-3 flex flex-wrap gap-4 text-sm text-zinc-600 dark:text-zinc-400">
          {parameters ? <span>Parameters: {parameters.toLocaleString()}</span> : null}
          {contextWindow ? <span>Context: {contextWindow.toLocaleString()}</span> : null}
          {report.model?.officialUrl ? (
            <a
              href={report.model.officialUrl}
              target="_blank"
              rel="noreferrer"
              className="text-teal-700 underline dark:text-teal-400"
            >
              Model card
            </a>
          ) : null}
        </div>
        <p className="mt-3 whitespace-pre-wrap text-zinc-700 dark:text-zinc-300">{report.analysis}</p>
      </header>

      <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Benchmarks</h2>
        {report.benchmarks.length === 0 ? (
          <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
            No benchmark scores were published on the model card.
          </p>
        ) : (
          <table className="mt-3 w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-200 dark:border-zinc-700">
                <th className="py-2">Benchmark</th>
                <th className="py-2">Score (0–100)</th>
                <th className="py-2">Source</th>
              </tr>
            </thead>
            <tbody>
              {report.benchmarks.map((row) => (
                <tr key={row.id} className="border-b border-zinc-100 dark:border-zinc-800">
                  <td className="py-2 font-medium">{row.benchmarkName}</td>
                  <td className="py-2">{row.score ?? "—"}</td>
                  <td className="py-2">
                    {row.sourceUrl ? (
                      <a
                        href={row.sourceUrl}
                        className="text-teal-700 underline dark:text-teal-400"
                        target="_blank"
                        rel="noreferrer"
                      >
                        {row.source}
                      </a>
                    ) : (
                      row.source
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <CapabilityTable capabilities={report.capabilities} flaws={report.flaws} />
      <ResourceChart resources={report.resources} />
      <ComparisonMatrix competitors={report.competitors} />
      <section className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Recommendations</h2>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-zinc-700 dark:text-zinc-300">
          {report.recommendations.length === 0 ? (
            <li>No recommendations yet.</li>
          ) : (
            report.recommendations.map((item) => <li key={item}>{item}</li>)
          )}
        </ul>
      </section>
      <ExportPanel report={report} jobId={jobId} />
    </div>
  );
}

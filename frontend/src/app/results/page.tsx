"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { ReportDashboard } from "@/components/ReportDashboard";
import { useModelAnalysis } from "@/hooks/useModelAnalysis";

function ResultsContent() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("jobId");
  const { result, error, isLoading } = useModelAnalysis(jobId);

  if (!jobId) {
    return (
      <p className="text-zinc-700 dark:text-zinc-300">
        Missing job id.{" "}
        <Link href="/" className="text-teal-700 underline dark:text-teal-400">
          Start a new analysis
        </Link>
        .
      </p>
    );
  }

  if (error) {
    return (
      <p role="alert" className="text-red-600 dark:text-red-400">
        {error}
      </p>
    );
  }

  if (isLoading || result === null || result.status === "queued" || result.status === "processing") {
    return (
      <p className="text-zinc-700 dark:text-zinc-300">
        Analysis {result?.status ?? "queued"}… polling job {jobId}.
      </p>
    );
  }

  if (result.status === "failed" || result.report === null) {
    return (
      <p role="alert" className="text-red-600 dark:text-red-400">
        Analysis failed. Return home and try again.
      </p>
    );
  }

  return <ReportDashboard report={result.report} jobId={jobId} />;
}

export default function ResultsPage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-4xl flex-col gap-6 px-6 py-12">
      <Link href="/" className="text-sm text-teal-700 hover:underline dark:text-teal-400">
        ← New analysis
      </Link>
      <Suspense fallback={<p>Loading results…</p>}>
        <ResultsContent />
      </Suspense>
    </main>
  );
}

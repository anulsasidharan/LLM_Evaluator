"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { analyzeModel } from "@/services/api";
import type { AnalysisDepth } from "@/types";

const DEPTH_OPTIONS: AnalysisDepth[] = ["quick", "standard", "detailed"];

export function ModelSearch() {
  const router = useRouter();
  const [modelName, setModelName] = useState("");
  const [depth, setDepth] = useState<AnalysisDepth>("standard");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = modelName.trim();
    if (!trimmed) {
      setError("Enter a model name to analyze.");
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      const job = await analyzeModel({ modelName: trimmed, depth });
      router.push(`/results?jobId=${job.jobId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start analysis. Is the API running?");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex w-full max-w-xl flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
    >
      <label className="flex flex-col gap-2 text-sm font-medium text-zinc-700 dark:text-zinc-200">
        Model name
        <input
          type="text"
          name="modelName"
          value={modelName}
          onChange={(event) => setModelName(event.target.value)}
          placeholder="e.g. claude-3-opus"
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-base font-normal text-zinc-900 outline-none ring-teal-600 focus:ring-2 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
        />
      </label>
      <label className="flex flex-col gap-2 text-sm font-medium text-zinc-700 dark:text-zinc-200">
        Analysis depth
        <select
          name="depth"
          value={depth}
          onChange={(event) => setDepth(event.target.value as AnalysisDepth)}
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-base font-normal text-zinc-900 outline-none ring-teal-600 focus:ring-2 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
        >
          {DEPTH_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
      {error ? (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      ) : null}
      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? "Starting analysis…" : "Analyze model"}
      </button>
    </form>
  );
}

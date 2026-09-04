"use client";

import { useEffect, useState } from "react";

import { getJobResult } from "@/services/api";
import type { JobResult, JobStatus } from "@/types";

const POLL_INTERVAL_MS = 2000;
const TERMINAL_STATUSES: JobStatus[] = ["completed", "failed"];

export interface UseModelAnalysisState {
  result: JobResult | null;
  error: string | null;
  isLoading: boolean;
}

export function useModelAnalysis(jobId: string | null): UseModelAnalysisState {
  const [result, setResult] = useState<JobResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(jobId));

  useEffect(() => {
    if (!jobId) {
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    let timeoutId: number | undefined;
    const id = jobId;

    async function tick(): Promise<void> {
      try {
        const next = await getJobResult(id);
        if (cancelled) {
          return;
        }
        setResult(next);
        setError(null);
        if (TERMINAL_STATUSES.includes(next.status)) {
          setIsLoading(false);
          return;
        }
        timeoutId = window.setTimeout(() => {
          void tick();
        }, POLL_INTERVAL_MS);
      } catch (err) {
        if (cancelled) {
          return;
        }
        setError(err instanceof Error ? err.message : "Failed to load analysis results.");
        setIsLoading(false);
      }
    }

    setIsLoading(true);
    void tick();

    return () => {
      cancelled = true;
      if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [jobId]);

  return { result, error, isLoading };
}

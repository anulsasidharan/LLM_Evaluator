import type { AnalyzeRequest, ApiResponse, JobAccepted, JobResult } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8002";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  const body = (await response.json()) as ApiResponse<T>;
  if (!response.ok || body.error || body.data === null) {
    const message = body.error?.message ?? `Request failed with status ${response.status}`;
    throw new Error(message);
  }
  return body.data;
}

export async function analyzeModel(payload: AnalyzeRequest): Promise<JobAccepted> {
  return request<JobAccepted>("/api/v1/models/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getJobResult(jobId: string): Promise<JobResult> {
  return request<JobResult>(`/api/v1/results/${jobId}`);
}

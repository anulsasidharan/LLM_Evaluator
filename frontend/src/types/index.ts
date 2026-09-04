export interface ErrorDetail {
  code: string;
  message: string;
}

export interface ApiResponse<T> {
  data: T | null;
  error: ErrorDetail | null;
}

export type AnalysisDepth = "quick" | "standard" | "detailed";
export type ExportFormat = "json" | "pdf" | "html";
export type JobStatus = "queued" | "processing" | "completed" | "failed";

export interface ModelSpecs {
  contextWindow: number | null;
  trainingDataCutoff: string | null;
  architecture: string | null;
  precision: string[];
}

export interface ModelProfile {
  id: string;
  name: string;
  vendor: string;
  version: string | null;
  parameters: number | null;
  releaseDate: string | null;
  description: string;
  officialUrl: string | null;
  tags: string[];
  specs: ModelSpecs;
  benchmarks: Record<string, unknown>;
  capabilities: Record<string, unknown>;
  flaws: string[];
  updatedAt: string;
}

export interface BenchmarkResult {
  id: string;
  modelId: string;
  benchmarkName: string;
  score: number | null;
  percentile: number | null;
  source: string;
  sourceUrl: string | null;
  metadata: Record<string, unknown>;
  recordedAt: string;
}

export interface HardwareTier {
  gpuMemory: string | null;
  cpuCores: number | null;
  ramGb: number | null;
  storageSsd: string | null;
  inferenceTime: string | null;
}

export interface ResourceRequirement {
  id: string;
  modelId: string;
  deploymentType: "local" | "cloud" | "edge";
  hostingOption: "ollama" | "vllm" | "llama.cpp" | null;
  requirements: {
    minimum: HardwareTier;
    optimal: HardwareTier;
    maximum: HardwareTier;
  };
}

export interface AnalyzeRequest {
  modelName: string;
  depth: AnalysisDepth;
  compareWith?: string[];
  includeResources?: boolean;
  exportFormat?: ExportFormat;
}

export interface JobAccepted {
  jobId: string;
  status: JobStatus;
  estimatedTimeSeconds: number;
  resultsUrl: string;
}

export interface AnalysisReport {
  model: ModelProfile | null;
  benchmarks: BenchmarkResult[];
  capabilities: Record<string, unknown>;
  flaws: string[];
  competitors: string[];
  resources: ResourceRequirement | null;
  analysis: string;
  recommendations: string[];
}

export interface JobResult {
  jobId: string;
  status: JobStatus;
  completedAt: string | null;
  report: AnalysisReport | null;
}

export interface ModelSearchHit {
  id: string;
  name: string;
  vendor: string;
  parameters: number | null;
  releaseDate: string | null;
  tags: string[];
}

export interface ModelSearchResponse {
  results: ModelSearchHit[];
  total: number;
}

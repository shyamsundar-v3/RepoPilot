export interface AnalyzeRequest {
  repo_url: string;
}

export interface ChatRequest {
  repo_id: string;
  question: string;
}

export interface EvidenceItem {
  file_path: string;
  line_range: string | null;
  snippet: string | null;
}

export interface Claim {
  text: string;
  evidence: EvidenceItem[];
  confidence: number;
}

export interface ReportSection {
  claims: Claim[];
}

export interface ReportResponse {
  repo_id: string;
  overview: ReportSection;
  architecture: ReportSection;
  code_flow: ReportSection;
  dependencies: ReportSection;
  docs: ReportSection;
  git_history: ReportSection;
  dev_guide: ReportSection;
  concerns: ReportSection;
}

export type TraceEventType =
  | "tool_call"
  | "tool_result"
  | "reviewer"
  | "done"
  | "error";

export interface TraceEvent {
  type: TraceEventType;
  agent: string | null;
  tool: string | null;
  input: Record<string, unknown> | null;
  output: string | null;
  message: string | null;
  timestamp: number | null;
}

export interface AnalyzeResponse {
  repo_id: string;
  job_id: string;
}

export interface ChatResponse {
  answer: string;
  evidence: EvidenceItem[];
  confidence: number;
}

export type JobStatus = "pending" | "running" | "done" | "error";

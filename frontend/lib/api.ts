import { AnalyzeRequest, AnalyzeResponse, ChatRequest, ChatResponse, ReportResponse } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

export function analyzeRepo(req: AnalyzeRequest): Promise<AnalyzeResponse> {
  return fetchJSON<AnalyzeResponse>(`${API}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export function getReport(repoId: string): Promise<ReportResponse> {
  return fetchJSON<ReportResponse>(`${API}/api/report/${repoId}`);
}

export function chatWithRepo(req: ChatRequest): Promise<ChatResponse> {
  return fetchJSON<ChatResponse>(`${API}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export function healthCheck(): Promise<{ status: string }> {
  return fetchJSON<{ status: string }>(`${API}/health`);
}

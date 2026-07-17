"use client";

import { useEffect, useState } from "react";
import { getReport } from "@/lib/api";
import { ReportResponse } from "@/lib/types";
import { downloadReportAsText } from "@/lib/exportReport";
import ReportTabs from "@/components/ReportTabs";
import ChatPanel from "@/components/ChatPanel";

export default function ReportPage({ params }: { params: { repoId: string } }) {
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retries, setRetries] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await getReport(params.repoId);
        if (!cancelled) setReport(data);
      } catch (e: any) {
        if (cancelled) return;
        const msg: string = e.message || "";
        // 502 means the backend job failed permanently — stop polling
        if (msg.startsWith("502:")) {
          const detail = msg.replace("502: ", "");
          try {
            const parsed = JSON.parse(detail);
            setError(parsed.detail || detail);
          } catch {
            setError(detail);
          }
        } else if (retries < 10) {
          // 404 means still processing — keep polling
          setTimeout(() => setRetries((r) => r + 1), 3000);
        } else {
          setError(msg);
        }
      }
    }
    load();
    return () => { cancelled = true; };
  }, [params.repoId, retries]);

  if (error) return <main className="p-8"><p className="text-red-400">{error}</p></main>;
  if (!report) return <main className="p-8"><p className="text-gray-400">Loading report...</p></main>;

  return (
    <main className="p-8 max-w-5xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Report: {params.repoId}</h1>
        <button
          onClick={() => downloadReportAsText(report, params.repoId)}
          className="px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-sm text-gray-200 hover:bg-gray-700 hover:border-gray-600 transition-colors"
        >
          Download as .txt
        </button>
      </div>
      <ReportTabs report={report} />
      <ChatPanel repoId={params.repoId} />
    </main>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import RepoInputForm from "@/components/RepoInputForm";
import AgentTraceLog from "@/components/AgentTraceLog";
import { useTraceSocket } from "@/lib/useTraceSocket";
import { analyzeRepo } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [repoId, setRepoId] = useState<string | null>(null);

  const { events, done } = useTraceSocket(jobId);

  async function handleSubmit(url: string) {
    setLoading(true);
    setError(null);
    try {
      const res = await analyzeRepo({ repo_url: url });
      setJobId(res.job_id);
      setRepoId(res.repo_id);
    } catch (e: any) {
      setError(e.message);
      setLoading(false);
    }
  }

  // Side effects (navigation) must not run directly in the render body —
  // calling router.push() there fires on every re-render while the
  // condition holds, instead of once when it first becomes true.
  useEffect(() => {
    if (done && repoId) {
      router.push(`/report/${repoId}`);
    }
  }, [done, repoId, router]);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 gap-8">
      <h1 className="text-4xl font-bold">RepoPilot</h1>
      <p className="text-gray-400 max-w-lg text-center">
        Paste a GitHub repo URL to get a full analysis — architecture, code flow,
        dependencies, concerns, and more.
      </p>
      <RepoInputForm onSubmit={handleSubmit} loading={loading} />
      {error && <p className="text-red-400">{error}</p>}
      {jobId && <AgentTraceLog events={events} />}
    </main>
  );
}

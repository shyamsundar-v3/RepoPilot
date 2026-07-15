"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { TraceEvent } from "./types";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export function useTraceSocket(jobId: string | null) {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [done, setDone] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  // Track `done` in a ref, not state, so the reconnect-on-close check always
  // sees the latest value without needing `done` in connect's dependency
  // array. Previously `done` was a useCallback dependency, so finishing a
  // job (setDone(true)) produced a *new* connect() identity, which retriggered
  // the outer effect and reopened a fresh websocket for an already-finished
  // job (it would then sit idle for up to 5 minutes before timing out).
  const doneRef = useRef(false);

  const connect = useCallback(() => {
    if (!jobId) return;
    const ws = new WebSocket(`${WS_BASE}/ws/trace/${jobId}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);

    ws.onmessage = (msg) => {
      try {
        const event: TraceEvent = JSON.parse(msg.data);
        setEvents((prev) => [...prev, event]);
        if (event.type === "done" || event.type === "error") {
          doneRef.current = true;
          setDone(true);
        }
      } catch {}
    };

    ws.onclose = () => {
      setConnected(false);
      if (!doneRef.current) {
        setTimeout(() => connect(), 2000);
      }
    };

    ws.onerror = () => ws.close();
  }, [jobId]);

  useEffect(() => {
    doneRef.current = false;
    setDone(false);
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return { events, connected, done };
}

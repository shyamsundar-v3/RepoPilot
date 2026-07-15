"use client";

import { TraceEvent } from "@/lib/types";

interface Props {
  events: TraceEvent[];
}

function eventIcon(type: string) {
  switch (type) {
    case "tool_call": return ">";
    case "tool_result": return "<";
    case "reviewer": return "?";
    case "done": return "*";
    case "error": return "!";
    default: return "-";
  }
}

function eventColor(type: string) {
  switch (type) {
    case "tool_call": return "text-blue-400";
    case "tool_result": return "text-green-400";
    case "reviewer": return "text-yellow-400";
    case "done": return "text-emerald-400";
    case "error": return "text-red-400";
    default: return "text-gray-400";
  }
}

export default function AgentTraceLog({ events }: Props) {
  return (
    <div className="bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto font-mono text-sm space-y-1">
      {events.length === 0 && (
        <p className="text-gray-500">Waiting for events...</p>
      )}
      {events.map((ev, i) => (
        <div key={i} className={`flex gap-2 ${eventColor(ev.type)}`}>
          <span className="w-4 text-center">{eventIcon(ev.type)}</span>
          <span className="text-gray-500">{ev.agent || ""}</span>
          <span>
            {ev.tool && <span className="text-gray-400">[{ev.tool}] </span>}
            {ev.message || ev.output?.slice(0, 120) || JSON.stringify(ev.input)?.slice(0, 120) || ""}
          </span>
        </div>
      ))}
    </div>
  );
}

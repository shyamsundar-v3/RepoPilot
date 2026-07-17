"use client";

import { useState } from "react";
import { EvidenceItem } from "@/lib/types";

interface Props {
  evidence: EvidenceItem[];
}

export default function EvidenceExpander({ evidence }: Props) {
  const [open, setOpen] = useState(false);

  if (evidence.length === 0) return null;

  return (
    <div className="mt-2">
      <button
        onClick={() => setOpen(!open)}
        className="text-xs text-blue-400 hover:text-blue-300"
      >
        {open ? "Hide" : "Show"} evidence ({evidence.length})
      </button>
      {open && (
        <div className="mt-2 space-y-2">
          {evidence.map((ev, i) => (
            <div key={i} className="bg-gray-800 rounded p-3 text-sm">
              <div className="text-gray-400 text-xs mb-1">
                {ev.file_path}
                {ev.line_range && <span> : {ev.line_range}</span>}
              </div>
              {ev.snippet && (
                <pre className="text-gray-300 text-xs overflow-x-auto whitespace-pre-wrap">
                  {ev.snippet}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

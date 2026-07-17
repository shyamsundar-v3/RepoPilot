"use client";

import { useState } from "react";
import { ReportResponse } from "@/lib/types";
import OverviewPanel from "./OverviewPanel";
import ArchitecturePanel from "./ArchitecturePanel";
import CodeFlowPanel from "./CodeFlowPanel";
import DependenciesPanel from "./DependenciesPanel";
import DocsPanel from "./DocsPanel";
import GitHistoryPanel from "./GitHistoryPanel";
import DevGuidePanel from "./DevGuidePanel";
import ConcernsPanel from "./ConcernsPanel";

const TABS = [
  { key: "overview", label: "Overview" },
  { key: "architecture", label: "Architecture" },
  { key: "code_flow", label: "Code Flow" },
  { key: "dependencies", label: "Dependencies" },
  { key: "docs", label: "Docs" },
  { key: "git_history", label: "Git History" },
  { key: "dev_guide", label: "Dev Guide" },
  { key: "concerns", label: "Concerns" },
] as const;

const PANELS: Record<string, React.FC<{ report: ReportResponse }>> = {
  overview: OverviewPanel,
  architecture: ArchitecturePanel,
  code_flow: CodeFlowPanel,
  dependencies: DependenciesPanel,
  docs: DocsPanel,
  git_history: GitHistoryPanel,
  dev_guide: DevGuidePanel,
  concerns: ConcernsPanel,
};

interface Props {
  report: ReportResponse;
}

export default function ReportTabs({ report }: Props) {
  const [active, setActive] = useState<string>("overview");
  const Panel = PANELS[active];

  return (
    <div>
      <div className="flex gap-1 border-b border-gray-700 mb-6 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActive(tab.key)}
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
              active === tab.key
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-gray-400 hover:text-gray-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {Panel && <Panel report={report} />}
    </div>
  );
}

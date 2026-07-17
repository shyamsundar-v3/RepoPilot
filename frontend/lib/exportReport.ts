import { ReportResponse, ReportSection } from "./types";

const SECTION_TITLES: { key: keyof Omit<ReportResponse, "repo_id">; title: string }[] = [
  { key: "overview", title: "OVERVIEW" },
  { key: "architecture", title: "ARCHITECTURE" },
  { key: "code_flow", title: "CODE FLOW" },
  { key: "dependencies", title: "DEPENDENCIES" },
  { key: "docs", title: "DOCS" },
  { key: "git_history", title: "GIT HISTORY" },
  { key: "dev_guide", title: "DEV GUIDE" },
  { key: "concerns", title: "CONCERNS" },
];

const RULE = "=".repeat(70);
const SUB_RULE = "-".repeat(70);

function formatSection(title: string, section: ReportSection): string {
  const lines: string[] = [RULE, title, RULE, ""];

  if (!section || section.claims.length === 0) {
    lines.push("No data available.", "");
    return lines.join("\n");
  }

  for (const claim of section.claims) {
    lines.push(claim.text.trim());
    lines.push(`\n[Confidence: ${Math.round(claim.confidence * 100)}%]`);

    if (claim.evidence.length > 0) {
      lines.push("", "Evidence:");
      for (const ev of claim.evidence) {
        const loc = ev.line_range ? `${ev.file_path}:${ev.line_range}` : ev.file_path;
        lines.push(`  - ${loc}`);
        if (ev.snippet) {
          const snippet = ev.snippet
            .split("\n")
            .map((l) => `      ${l}`)
            .join("\n");
          lines.push(snippet);
        }
      }
    }
    lines.push("", SUB_RULE, "");
  }

  return lines.join("\n");
}

export function reportToPlainText(report: ReportResponse, repoId: string): string {
  const parts: string[] = [
    RULE,
    `REPOPILOT REPORT: ${repoId}`,
    `Generated: ${new Date().toISOString()}`,
    RULE,
    "",
  ];

  for (const { key, title } of SECTION_TITLES) {
    parts.push(formatSection(title, report[key] as ReportSection));
  }

  return parts.join("\n").trimEnd() + "\n";
}

export function downloadReportAsText(report: ReportResponse, repoId: string) {
  const text = reportToPlainText(report, repoId);
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = `repopilot-report-${repoId}.txt`;
  document.body.appendChild(a);
  a.click();
  a.remove();

  URL.revokeObjectURL(url);
}

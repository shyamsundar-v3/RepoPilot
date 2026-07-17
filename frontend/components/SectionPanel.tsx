import { ReportSection } from "@/lib/types";
import ConfidenceBadge from "./ConfidenceBadge";
import EvidenceExpander from "./EvidenceExpander";

interface Props {
  title: string;
  section: ReportSection;
  cautionLabel?: boolean;
}

export default function SectionPanel({ title, section, cautionLabel }: Props) {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        {title}
        {cautionLabel && (
          <span className="text-xs bg-orange-500/20 text-orange-400 px-2 py-0.5 rounded">
            potential
          </span>
        )}
      </h2>
      {section.claims.length === 0 && (
        <p className="text-gray-500">No data available.</p>
      )}
      <div className="space-y-4">
        {section.claims.map((claim, i) => (
          <div key={i} className="bg-gray-900 rounded-lg p-4 border border-gray-800">
            <div className="flex items-start justify-between gap-3">
              <p className="text-gray-200 whitespace-pre-wrap">{claim.text}</p>
              <ConfidenceBadge confidence={claim.confidence} />
            </div>
            <EvidenceExpander evidence={claim.evidence} />
          </div>
        ))}
      </div>
    </div>
  );
}

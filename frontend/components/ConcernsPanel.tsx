import { ReportResponse } from "@/lib/types";
import SectionPanel from "./SectionPanel";

export default function ConcernsPanel({ report }: { report: ReportResponse }) {
  return <SectionPanel title="Concerns" section={report.concerns} cautionLabel />;
}

import { ReportResponse } from "@/lib/types";
import SectionPanel from "./SectionPanel";

export default function DevGuidePanel({ report }: { report: ReportResponse }) {
  return <SectionPanel title="Developer Guide" section={report.dev_guide} />;
}

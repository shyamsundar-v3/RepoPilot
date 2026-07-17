import { ReportResponse } from "@/lib/types";
import SectionPanel from "./SectionPanel";

export default function DocsPanel({ report }: { report: ReportResponse }) {
  return <SectionPanel title="Documentation" section={report.docs} />;
}

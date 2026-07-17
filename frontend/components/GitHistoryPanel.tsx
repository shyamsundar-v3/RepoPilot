import { ReportResponse } from "@/lib/types";
import SectionPanel from "./SectionPanel";

export default function GitHistoryPanel({ report }: { report: ReportResponse }) {
  return <SectionPanel title="Git History" section={report.git_history} />;
}

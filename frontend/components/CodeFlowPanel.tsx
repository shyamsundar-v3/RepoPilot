import { ReportResponse } from "@/lib/types";
import SectionPanel from "./SectionPanel";

export default function CodeFlowPanel({ report }: { report: ReportResponse }) {
  return <SectionPanel title="Code Flow" section={report.code_flow} />;
}

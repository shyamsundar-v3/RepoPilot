import { ReportResponse } from "@/lib/types";
import SectionPanel from "./SectionPanel";

export default function OverviewPanel({ report }: { report: ReportResponse }) {
  return <SectionPanel title="Overview" section={report.overview} />;
}

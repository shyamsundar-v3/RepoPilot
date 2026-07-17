import { ReportResponse } from "@/lib/types";
import SectionPanel from "./SectionPanel";

export default function DependenciesPanel({ report }: { report: ReportResponse }) {
  return <SectionPanel title="Dependencies" section={report.dependencies} />;
}

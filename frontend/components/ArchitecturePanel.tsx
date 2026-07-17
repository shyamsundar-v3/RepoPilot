import { ReportResponse } from "@/lib/types";
import SectionPanel from "./SectionPanel";

export default function ArchitecturePanel({ report }: { report: ReportResponse }) {
  return <SectionPanel title="Architecture" section={report.architecture} />;
}

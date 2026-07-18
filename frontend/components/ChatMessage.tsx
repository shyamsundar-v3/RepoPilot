import { ChatResponse } from "@/lib/types";
import ConfidenceBadge from "./ConfidenceBadge";
import EvidenceExpander from "./EvidenceExpander";

interface Props {
  role: "user" | "assistant";
  text: string;
  response?: ChatResponse;
}

export default function ChatMessage({ role, text, response }: Props) {
  if (role === "user") {
    return (
      <div className="flex justify-end">
        <div className="bg-blue-600 rounded-lg px-4 py-2 max-w-lg">
          <p className="text-white">{text}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="bg-gray-800 rounded-lg px-4 py-3 max-w-2xl border border-gray-700">
        <div className="flex items-start justify-between gap-3">
          <p className="text-gray-200 whitespace-pre-wrap">{text}</p>
          {response && <ConfidenceBadge confidence={response.confidence} />}
        </div>
        {response && <EvidenceExpander evidence={response.evidence} />}
      </div>
    </div>
  );
}

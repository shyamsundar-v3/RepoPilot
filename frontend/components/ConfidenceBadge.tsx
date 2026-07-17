interface Props {
  confidence: number;
}

export default function ConfidenceBadge({ confidence }: Props) {
  const pct = Math.round(confidence * 100);
  let color = "bg-red-500/20 text-red-400";
  if (pct >= 80) color = "bg-emerald-500/20 text-emerald-400";
  else if (pct >= 50) color = "bg-yellow-500/20 text-yellow-400";

  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {pct}%
    </span>
  );
}

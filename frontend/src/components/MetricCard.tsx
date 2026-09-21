import { Card, CardLabel } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function MetricCard({
  label,
  value,
  sublabel,
  tone,
}: {
  label: string;
  value: string;
  sublabel?: string;
  tone?: "good" | "warn" | "danger";
}) {
  return (
    <Card>
      <CardLabel>{label}</CardLabel>
      <div
        className={cn(
          "num mt-1.5 text-2xl font-bold tracking-[-0.02em]",
          tone === "good" && "text-good",
          tone === "warn" && "text-warn",
          tone === "danger" && "text-danger",
          !tone && "text-snow",
        )}
      >
        {value}
      </div>
      {sublabel && <div className="mt-1 text-xs text-mist">{sublabel}</div>}
    </Card>
  );
}

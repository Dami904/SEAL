import Link from "next/link";
import { cn } from "@/lib/utils";
import { SUPPORTED_SYMBOLS, type SupportedSymbol } from "@/lib/api";

const LABELS: Record<SupportedSymbol, string> = {
  rtsla: "rTSLA",
  rnvda: "rNVDA",
  raapl: "rAAPL",
  ramzn: "rAMZN",
  rmsft: "rMSFT",
};

export function SymbolSwitcher({ basePath, active }: { basePath: string; active: SupportedSymbol }) {
  return (
    <div
      className="inline-flex items-center gap-1 rounded-full border border-white/[0.08] bg-white/[0.035] p-1.5"
      aria-label="Symbol"
    >
      {SUPPORTED_SYMBOLS.map((s) => (
        <Link
          key={s}
          href={`${basePath}?symbol=${s}`}
          className={cn(
            "rounded-full px-3 py-1 font-mono text-xs font-medium transition-all duration-200 ease-out",
            s === active
              ? "border border-white/[0.14] bg-white/[0.12] text-snow"
              : "text-snow/70 hover:bg-white/[0.06] hover:text-snow",
          )}
        >
          {LABELS[s]}
        </Link>
      ))}
    </div>
  );
}

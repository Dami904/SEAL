"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/backtest", label: "Backtest" },
  { href: "/forecast", label: "Forecast" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50">
      <div className="border-b border-white/[0.06] bg-ink/65 backdrop-blur-2xl">
        <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6">
          <Link href="/backtest" className="flex items-center gap-2.5" aria-label="SEAL">
            <span className="font-display text-[17px] font-bold tracking-[-0.03em] text-snow">
              SEAL
            </span>
            <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-mist/70">
              Alpha Factory
            </span>
          </Link>

          <nav
            className="flex items-center gap-1 rounded-full border border-white/[0.08] bg-white/[0.035] p-1.5 backdrop-blur-2xl"
            aria-label="Primary navigation"
          >
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-full px-4 py-1.5 text-sm font-medium transition-all duration-200 ease-out",
                  pathname === item.href
                    ? "border border-white/[0.14] bg-white/[0.12] text-snow"
                    : "text-snow/80 hover:bg-white/[0.06] hover:text-snow",
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}

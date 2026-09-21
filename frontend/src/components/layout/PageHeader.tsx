import { cn } from "@/lib/utils";

export function PageHeader({
  kicker,
  title,
  description,
  className,
}: {
  kicker?: string;
  title: string;
  description: string;
  className?: string;
}) {
  return (
    <div className={cn("animate-fade-up", className)}>
      {kicker && (
        <span className="inline-flex items-center rounded-full border border-white/[0.1] bg-white/[0.04] px-3 py-1 font-mono text-[11px] font-medium uppercase tracking-[0.16em] text-mist/90 backdrop-blur-md">
          {kicker}
        </span>
      )}
      <h1
        className={cn(
          "font-display text-3xl font-extrabold tracking-[-0.035em] text-snow sm:text-4xl",
          kicker && "mt-3",
        )}
      >
        {title}
      </h1>
      <p className="mt-3 max-w-2xl text-sm font-light leading-relaxed text-mist">
        {description}
      </p>
    </div>
  );
}

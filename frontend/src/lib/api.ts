const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8787";

export const SUPPORTED_SYMBOLS = ["rtsla", "rnvda", "raapl", "ramzn", "rmsft"] as const;
export type SupportedSymbol = (typeof SUPPORTED_SYMBOLS)[number];

export interface ForecastBlock {
  count: number;
  mae_pct: number;
  directional_count: number;
  directional_accuracy: number | null;
}

export interface HeadlineMetrics {
  trade_count: number;
  total_pnl: number;
  sharpe: number;
  sortino: number;
  max_drawdown: number;
  turnover: number;
  forecast: ForecastBlock;
}

export interface SplitMetrics {
  split_date: string;
  in_sample: HeadlineMetrics;
  out_of_sample: HeadlineMetrics;
  oos_decay_ratio: number | null;
  oos_decay_flag: boolean;
}

export interface CostGap {
  clipped: { total_pnl: number; sharpe: number };
  one_shot: { total_pnl: number; sharpe: number };
  pnl_improvement: number;
}

export interface BacktestSummary {
  data_path: string;
  symbol: string;
  equity_curve: Array<{ timestamp: string; equity: number }>;
  headline: HeadlineMetrics;
  in_sample_out_of_sample: SplitMetrics | null;
  rolling_30day_sharpe: Array<{ date: string; sharpe: number }>;
  one_shot_vs_clipped: CostGap;
}

export async function fetchBacktestSummary(
  symbol: SupportedSymbol = "rtsla",
): Promise<BacktestSummary | null> {
  try {
    const res = await fetch(`${API_BASE}/backtest/summary?symbol=${symbol}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as BacktestSummary;
  } catch {
    return null;
  }
}

export interface ForecastResponse {
  symbol: string;
  spread: number;
  side: "long" | "short" | null;
  impliedOpen: number;
}

export async function fetchForecast(params: {
  symbol: string;
  rtokenPrice: number;
  cashClose: number;
  event: boolean;
}): Promise<ForecastResponse | null> {
  const qs = new URLSearchParams({
    symbol: params.symbol,
    rtokenPrice: String(params.rtokenPrice),
    cashClose: String(params.cashClose),
    event: String(params.event),
  });
  try {
    const res = await fetch(`${API_BASE}/forecast?${qs.toString()}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as ForecastResponse;
  } catch {
    return null;
  }
}

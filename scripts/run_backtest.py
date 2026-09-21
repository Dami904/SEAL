import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml

from seal.backtest import cost_gap, rolling_sharpe, run_backtest, split_metrics
from seal.data import load_series
from seal.params import Params


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    params = Params.from_dict(config)
    data_path = ROOT / config["data_path"]
    df = load_series(str(data_path))

    result = run_backtest(df, params, seed=args.seed)
    metrics = result.metrics()

    split_date = config.get("split_date")
    split = split_metrics(df, params, split_date, seed=args.seed) if split_date else None
    rolling = rolling_sharpe(result, window_days=30)
    gap = cost_gap(df, params, seed=args.seed)

    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    result.equity_curve.to_csv(reports_dir / "equity_curve.csv", index=False)

    equity_curve = [
        {"timestamp": row["timestamp"].isoformat(), "equity": float(row["equity"])}
        for _, row in result.equity_curve.iterrows()
    ]

    report = {
        "data_path": config["data_path"],
        "symbol": params.symbol,
        "equity_curve": equity_curve,
        "headline": metrics,
        "in_sample_out_of_sample": split,
        "rolling_30day_sharpe": rolling,
        "one_shot_vs_clipped": gap,
    }
    (reports_dir / "backtest_summary.json").write_text(json.dumps(report, indent=2))

    lines = [
        "# Backtest summary",
        "",
        f"- Data: `{config['data_path']}`",
        f"- Symbol: {params.symbol}",
        f"- Trades: {metrics['trade_count']}",
        f"- Total PnL: {metrics['total_pnl']:.2f}",
        f"- Sharpe: {metrics['sharpe']:.2f}",
        f"- Sortino: {metrics['sortino']:.2f}",
        f"- Max drawdown: {metrics['max_drawdown']:.2f}",
        f"- Turnover: {metrics['turnover']:.2f}",
        f"- Forecast MAE: {metrics['forecast']['mae_pct']:.4%} (n={metrics['forecast']['count']}), "
        f"directional accuracy="
        + (f"{metrics['forecast']['directional_accuracy']:.1%}"
           if metrics['forecast']['directional_accuracy'] is not None else "n/a")
        + f" (n={metrics['forecast']['directional_count']})",
        "",
    ]
    if split:
        lines += [
            f"## In-sample / out-of-sample (split {split['split_date']})",
            "",
            f"- IS Sharpe: {split['in_sample']['sharpe']:.2f} "
            f"({split['in_sample']['trade_count']} trades)",
            f"- OOS Sharpe: {split['out_of_sample']['sharpe']:.2f} "
            f"({split['out_of_sample']['trade_count']} trades)",
            f"- OOS/IS decay ratio: {split['oos_decay_ratio']}"
            f"{' — WARNING: below 0.5x reference' if split['oos_decay_flag'] else ''}",
            "",
        ]
    lines += [
        "## One-shot vs. clipped execution",
        "",
        f"- Clipped: PnL {gap['clipped']['total_pnl']:.2f}, Sharpe {gap['clipped']['sharpe']:.2f}",
        f"- One-shot: PnL {gap['one_shot']['total_pnl']:.2f}, Sharpe {gap['one_shot']['sharpe']:.2f}",
        f"- Improvement from clipping: {gap['pnl_improvement']:.2f}",
        "",
    ]
    summary_path = reports_dir / "backtest_summary.md"
    summary_path.write_text("\n".join(lines))

    print("\n".join(lines))


if __name__ == "__main__":
    main()

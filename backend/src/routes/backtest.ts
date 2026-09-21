import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import type { FastifyInstance } from "fastify";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPORT_PATH = path.resolve(HERE, "../../../reports/backtest_summary.json");
// Pinned real snapshot, committed (not gitignored like reports/) — lets a
// deployed instance serve real data without running the Python backtest at
// deploy time. Always prefer the fresh report when one exists on disk.
const SEED_PATH = path.resolve(HERE, "../../seed/backtest_summary.json");

export function registerBacktestRoute(app: FastifyInstance): void {
  app.get("/backtest/summary", async (_request, reply) => {
    for (const p of [REPORT_PATH, SEED_PATH]) {
      try {
        const raw = await readFile(p, "utf-8");
        reply.send(JSON.parse(raw));
        return;
      } catch {
        continue;
      }
    }
    reply.code(404).send({
      error: "backtest_summary.json not found — run " +
        "`python scripts/run_backtest.py --config configs/default.yaml` first.",
    });
  });
}

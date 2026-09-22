import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import type { FastifyInstance } from "fastify";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPORTS_DIR = path.resolve(HERE, "../../../reports");
// Pinned real snapshots, committed (not gitignored like reports/) — let a
// deployed instance serve real data without running the Python backtest at
// deploy time. Always prefer the fresh report when one exists on disk.
const SEED_DIR = path.resolve(HERE, "../../seed");

// Allowlist — the slug drives a filesystem path, never pass it through raw.
export const SUPPORTED_SYMBOLS = ["rtsla", "rnvda", "raapl", "ramzn", "rmsft"] as const;
const DEFAULT_SYMBOL = "rtsla";

interface BacktestQuery {
  symbol?: string;
}

export function registerBacktestRoute(app: FastifyInstance): void {
  app.get<{ Querystring: BacktestQuery }>("/backtest/summary", async (request, reply) => {
    const requested = request.query.symbol?.toLowerCase() ?? DEFAULT_SYMBOL;
    if (!SUPPORTED_SYMBOLS.includes(requested as (typeof SUPPORTED_SYMBOLS)[number])) {
      reply.code(400).send({
        error: `Unknown symbol "${requested}". Supported: ${SUPPORTED_SYMBOLS.join(", ")}.`,
      });
      return;
    }

    for (const dir of [REPORTS_DIR, SEED_DIR]) {
      try {
        const raw = await readFile(path.join(dir, `${requested}_summary.json`), "utf-8");
        reply.send(JSON.parse(raw));
        return;
      } catch {
        continue;
      }
    }
    reply.code(404).send({
      error: `${requested}_summary.json not found — run ` +
        `\`python scripts/run_backtest.py --config configs/${requested === DEFAULT_SYMBOL ? "default" : requested}.yaml\` first.`,
    });
  });
}

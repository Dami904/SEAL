import type { FastifyInstance } from "fastify";
import { computeSpread, parentSide } from "../signal.js";
import { impliedFairValue } from "../forecast.js";

const DEFAULT_ENTRY_THRESHOLD = 0.015; // matches configs/default.yaml entry_threshold

interface ForecastQuery {
  symbol?: string;
  rtokenPrice?: string;
  cashClose?: string;
  event?: string;
  threshold?: string;
}

export function registerForecastRoute(app: FastifyInstance): void {
  app.get<{ Querystring: ForecastQuery }>("/forecast", async (request, reply) => {
    const { symbol, rtokenPrice, cashClose, event, threshold } = request.query;

    const rtoken = Number(rtokenPrice);
    const cash = Number(cashClose);
    const entryThreshold = threshold !== undefined ? Number(threshold) : DEFAULT_ENTRY_THRESHOLD;
    if (!symbol || !Number.isFinite(rtoken) || !Number.isFinite(cash) || cash <= 0
        || !Number.isFinite(entryThreshold)) {
      reply.code(400).send({
        error: "symbol, rtokenPrice, cashClose are required; cashClose must be positive.",
      });
      return;
    }

    const isEvent = event === "true" || event === "1";
    const spread = computeSpread(rtoken, cash);
    const side = parentSide(spread, entryThreshold, isEvent);
    const impliedOpen = impliedFairValue(rtoken, cash, isEvent);

    reply.send({ symbol, spread, side, impliedOpen });
  });
}

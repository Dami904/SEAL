import { fileURLToPath } from "node:url";
import Fastify from "fastify";
import cors from "@fastify/cors";
import { registerBacktestRoute } from "./routes/backtest.js";
import { registerForecastRoute } from "./routes/forecast.js";

export function buildApp() {
  const app = Fastify({ logger: true });

  app.register(cors, {
    origin: process.env.FRONTEND_URL ?? "http://localhost:3000",
  });

  app.get("/health", async () => ({ status: "ok" }));
  registerBacktestRoute(app);
  registerForecastRoute(app);

  return app;
}

async function main() {
  const app = buildApp();
  const port = Number(process.env.PORT ?? 8787);
  await app.listen({ port, host: "0.0.0.0" });
}

const isMain = process.argv[1] !== undefined && fileURLToPath(import.meta.url) === process.argv[1];
if (isMain) {
  main().catch((err) => {
    console.error(err);
    process.exit(1);
  });
}

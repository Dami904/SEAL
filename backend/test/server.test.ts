import { describe, expect, it } from "vitest";
import { buildApp } from "../src/server.js";

describe("routes", () => {
  it("GET /health", async () => {
    const app = buildApp();
    const res = await app.inject({ method: "GET", url: "/health" });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toEqual({ status: "ok" });
  });

  it("GET /forecast rejects missing params", async () => {
    const app = buildApp();
    const res = await app.inject({ method: "GET", url: "/forecast" });
    expect(res.statusCode).toBe(400);
  });

  it("GET /forecast computes spread/side/impliedOpen", async () => {
    const app = buildApp();
    const res = await app.inject({
      method: "GET",
      url: "/forecast?symbol=rTSLA&rtokenPrice=340&cashClose=330&event=true",
    });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.symbol).toBe("rTSLA");
    expect(body.spread).toBeCloseTo(340 / 330 - 1);
    expect(body.side).toBe("long");
    expect(body.impliedOpen).toBe(340);
  });

  it("GET /backtest/summary returns the real report", async () => {
    const app = buildApp();
    const res = await app.inject({ method: "GET", url: "/backtest/summary" });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.symbol).toBe("rTSLA");
    expect(body.headline.trade_count).toBeGreaterThan(0);
  });
});

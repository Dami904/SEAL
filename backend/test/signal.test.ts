import { describe, expect, it } from "vitest";
import { computeSpread, isEventWindow, parentSide } from "../src/signal.js";

describe("computeSpread", () => {
  it("computes signed spread", () => {
    expect(computeSpread(110, 100)).toBeCloseTo(0.1);
    expect(computeSpread(90, 100)).toBeCloseTo(-0.1);
  });

  it("rejects non-positive cashClose", () => {
    expect(() => computeSpread(100, 0)).toThrow();
  });
});

describe("isEventWindow", () => {
  it("checks membership", () => {
    const dates = new Set(["2026-01-29"]);
    expect(isEventWindow("2026-01-29", dates)).toBe(true);
    expect(isEventWindow("2026-01-30", dates)).toBe(false);
  });
});

describe("parentSide", () => {
  it("returns null below threshold", () => {
    expect(parentSide(0.01, 0.015, false)).toBeNull();
  });

  it("trades with the move on an event", () => {
    expect(parentSide(0.02, 0.015, true)).toBe("long");
    expect(parentSide(-0.02, 0.015, true)).toBe("short");
  });

  it("fades the move without an event", () => {
    expect(parentSide(0.02, 0.015, false)).toBe("short");
    expect(parentSide(-0.02, 0.015, false)).toBe("long");
  });
});

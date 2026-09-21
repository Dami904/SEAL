/** Fixture values computed from seal/signal.py (Python) on the same inputs
 * — regenerate by running the snippet in the commit that added this file
 * if seal/signal.py's logic ever changes. Pins the TS port to the Python
 * implementation so the two can't silently drift. */
import { describe, expect, it } from "vitest";
import { computeSpread, isEventWindow, parentSide } from "../src/signal.js";

const CASES: Array<{
  rtoken: number;
  cash: number;
  threshold: number;
  date: string;
  eventDates: string[];
  expectedSpread: number;
  expectedIsEvent: boolean;
  expectedSide: "long" | "short" | null;
}> = [
  { rtoken: 110, cash: 100, threshold: 0.015, date: "2026-01-01", eventDates: ["2026-01-01"],
    expectedSpread: 0.1, expectedIsEvent: true, expectedSide: "long" },
  { rtoken: 90, cash: 100, threshold: 0.015, date: "2026-01-02", eventDates: ["2026-01-01"],
    expectedSpread: -0.1, expectedIsEvent: false, expectedSide: "long" },
  { rtoken: 101, cash: 100, threshold: 0.015, date: "2026-01-01", eventDates: [],
    expectedSpread: 0.01, expectedIsEvent: false, expectedSide: null },
  { rtoken: 98.5, cash: 100, threshold: 0.015, date: "2026-01-01", eventDates: [],
    expectedSpread: -0.015, expectedIsEvent: false, expectedSide: "long" },
  { rtoken: 104, cash: 100, threshold: 0.02, date: "2026-01-01", eventDates: ["2026-01-01"],
    expectedSpread: 0.04, expectedIsEvent: true, expectedSide: "long" },
  { rtoken: 96, cash: 100, threshold: 0.02, date: "2026-01-01", eventDates: ["2026-01-01"],
    expectedSpread: -0.04, expectedIsEvent: true, expectedSide: "short" },
];

describe("TS signal port matches Python seal/signal.py", () => {
  for (const c of CASES) {
    it(`rtoken=${c.rtoken} cash=${c.cash} thr=${c.threshold} date=${c.date}`, () => {
      const spread = computeSpread(c.rtoken, c.cash);
      const isEvent = isEventWindow(c.date, new Set(c.eventDates));
      const side = parentSide(spread, c.threshold, isEvent);

      expect(spread).toBeCloseTo(c.expectedSpread, 10);
      expect(isEvent).toBe(c.expectedIsEvent);
      expect(side).toBe(c.expectedSide);
    });
  }
});

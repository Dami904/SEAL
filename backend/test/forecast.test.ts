import { describe, expect, it } from "vitest";
import { impliedFairValue } from "../src/forecast.js";

describe("impliedFairValue", () => {
  it("trusts the print on an event (follow)", () => {
    expect(impliedFairValue(104, 100, true)).toBe(104);
  });

  it("trusts the prior close without an event (fade)", () => {
    expect(impliedFairValue(104, 100, false)).toBe(100);
  });
});

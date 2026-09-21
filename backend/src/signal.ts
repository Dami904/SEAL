/** Direct TS port of seal/signal.py — same names, same behavior. Pinned to
 * the Python implementation by test/golden.test.ts. */

export type Side = "long" | "short" | null;

export function computeSpread(rtokenPrice: number, cashClose: number): number {
  if (cashClose <= 0) {
    throw new Error("cashClose must be positive");
  }
  return rtokenPrice / cashClose - 1.0;
}

export function isEventWindow(date: string, eventDates: ReadonlySet<string>): boolean {
  return eventDates.has(date);
}

export function parentSide(spread: number, threshold: number, isEvent: boolean): Side {
  if (Math.abs(spread) < threshold) {
    return null;
  }
  const movedUp = spread > 0;
  const tradeWithMove = isEvent ? movedUp : !movedUp;
  return tradeWithMove ? "long" : "short";
}

/** The reframe: the same signal that decides a trade's side, exposed as an
 * implied pre-open fair-value forecast instead of only a trade decision.
 * "Follow" (event-corroborated) trusts the print; "fade" (no event) trusts
 * the last real cash close. Mirrors seal/backtest.py's forecast_price
 * assignment exactly. */

export function impliedFairValue(rtokenPrice: number, cashClose: number, isEvent: boolean): number {
  return isEvent ? rtokenPrice : cashClose;
}

# Threat model

Who's trusted, and what happens if each credential in scope is compromised.

## Credentials currently in scope

| Credential | Used for | Scope | If compromised |
|---|---|---|---|
| Bitget Playbook key (user's own, never committed) | Only if the Playbook package is published later, per `docs/PLAYBOOK_PUBLISH.md` — not used by anything in this repo today | Playbook account only — distinct from any exchange trading API key | Attacker could publish/overwrite Playbook strategies under the user's account. No funds are reachable through this key. |

No other credential is in scope. No credential is committed: `.env` files
are gitignored, and the code reads only non-secret configuration from the
environment (`FRONTEND_URL`, `PORT`, `NEXT_PUBLIC_API_URL`). The repo holds no
exchange API key, no wallet and no private key, and its code makes no
authenticated external calls — the Bitget market-data API used for rToken
candles is public and keyless, `bitget-mcp-server`'s documented install
requires no key, and no live execution client exists (see
`docs/API_NOTES.md`).

## What is explicitly NOT in scope, and why

- **No wallet.** SEAL never signs a transaction, never holds a private key,
  and has no on-chain component. rTokens are mainnet-only (Arbitrum/Morph)
  with no testnet — holding or settling them on-chain would be a
  materially different, higher-stakes integration this repo deliberately
  does not attempt.
- **No exchange trading API key.** rToken prices come from Bitget's
  public market-data API and stock prices from `bitget-mcp-server`, both
  read-only and keyless. No order is ever placed — `seal/backtest.py`
  simulates fills against historical market data only.
- **No mainnet exposure.** Nothing in this repo deploys to or transacts on
  mainnet. The only sanctioned path for future live
  execution is Bitget Agent Hub's `--paper-trading` Demo environment (its
  own separate Demo API key, no real funds) — not implemented here.

## If this changes later

Before adding any live execution path (even paper trading), update this
file with: what the paper-trading Demo API key can do, its blast radius if
leaked (should be zero real funds by construction of Bitget's Demo
environment, but verify rather than assume), and how it's stored (never
committed, never read from `.env*` by an agent session).

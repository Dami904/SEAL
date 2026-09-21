# Threat model

Who's trusted, and what happens if each credential in scope is compromised.

## Credentials currently in scope

| Credential | Used for | Scope | If compromised |
|---|---|---|---|
| Bitget Playbook API key (user's own, not held by this repo) | Publishing the backtest to Bitget Playbook's sandbox, per `docs/PLAYBOOK_PUBLISH.md` | Playbook account only — distinct from any exchange trading API key | Attacker could publish/overwrite Playbook strategies under the user's account. No funds are reachable through this key. |

No other credential is in scope. This repo holds no `.env`, no exchange API
key, no wallet, no private key, and makes no authenticated external calls —
`bitget-mcp-server`'s documented install requires none, and no live
execution client exists (see `docs/API_NOTES.md`).

## What is explicitly NOT in scope, and why

- **No wallet.** SEAL never signs a transaction, never holds a private key,
  and has no on-chain component. rTokens are mainnet-only (Arbitrum/Morph)
  with no testnet — holding or settling them on-chain would be a
  materially different, higher-stakes integration this repo deliberately
  does not attempt.
- **No exchange trading API key.** All price data comes from
  `bitget-mcp-server` (read-only, no key). No order is ever placed —
  `seal/backtest.py` simulates fills against historical/modeled data only.
- **No mainnet exposure.** Per CLAUDE.md, nothing in this repo deploys to
  or transacts on mainnet. The only sanctioned path for future live
  execution is Bitget Agent Hub's `--paper-trading` Demo environment (its
  own separate Demo API key, no real funds) — not implemented here.

## If this changes later

Before adding any live execution path (even paper trading), update this
file with: what the paper-trading Demo API key can do, its blast radius if
leaked (should be zero real funds by construction of Bitget's Demo
environment, but verify rather than assume), and how it's stored (never
committed, never read from `.env*` by an agent session, per CLAUDE.md).

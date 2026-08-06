# Pinterest

This folder is for Pinterest ads investigations and change logs.

## Structure

- `scripts/` Pinterest API reporting and management commands when introduced
- `config/` Pinterest reporting definitions and operational guardrails when introduced
- `investigations/` dated setup and performance reviews
- `changes/` dated budget and campaign change logs

Keep all Pinterest-specific API calls in this folder. Commands that change live
campaigns must use explicit operator confirmation, channel guardrails, and a
dated record in `changes/`.

Shared audience generation and run notes live in `../audiences/` because the same customer lists can support Pinterest, Google, and future advertising platforms.

## Current Campaign Direction

As of August 6, 2026, `2025-11-15 04:36 UTC | Catalog sales`
(`626757012436`) is the active Pinterest revenue campaign after its budget was
increased from `$115/day` to `$140/day`. `Consideration Campaign | 2026-05-14
17:21 UTC` (`626758545818`) is paused after producing no directly attributed
checkout revenue during the reviewed period. The dated rationale and metrics
are recorded in
`changes/2026-08-06-consideration-pause-catalog-budget-increase.md`.

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

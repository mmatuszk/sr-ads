# Pinterest Consideration Pause and Catalog Budget Increase

Date: 2026-08-06

## Scope

This note records two changes made manually in Pinterest Campaign Manager:

- paused `Consideration Campaign | 2026-05-14 17:21 UTC`
  - objective: Consideration
  - campaign ID: `626758545818`
- kept `2025-11-15 04:36 UTC | Catalog sales` active and increased its daily
  budget
  - objective: Catalog sales
  - campaign ID: `626757012436`
  - previous daily budget: `$115/day`
  - new daily budget: `$140/day`
  - increase: `$25/day` (`21.7%`)

## Rationale

The Consideration campaign was paused because it had generated no directly
attributed checkout revenue, and the active Catalog sales campaign did not show
the hoped-for improvement while the Consideration campaign was running. The
Catalog sales campaign remained the direct revenue-producing campaign, so
budget was concentrated there.

This is an operating decision based on observed performance. It does not claim
that the Consideration campaign caused the Catalog sales campaign's weaker
performance, and it does not rule out unmeasured view-through or assisted
effects.

## Performance Snapshot

Pinterest Campaign Manager screenshot captured August 6, 2026, using `Last 30
days` and UTC reporting:

| Campaign | Status | Spend | Checkout ROAS | Checkout order value | Checkout conversions | Checkout CPA |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Consideration (`626758545818`) | Paused | `$1,500.35` | `0.00` | `$0.00` | `0` | Not meaningful with zero conversions |
| Catalog sales (`626757012436`) | Active | `$3,447.61` | `2.11` | `$7,272.35` | `62` | `$55.61` |
| Account total shown | — | `$4,947.96` | `1.47` | `$7,272.35` | `62` | `$79.81` |

The screenshot also showed checkout conversion rates of `0%` for Consideration,
`0.03%` for Catalog sales, and `0.02%` for the displayed account total.

## Follow-up

Use the Catalog sales campaign as the active Pinterest revenue campaign. Review
spend, checkout order value, ROAS, conversion count, and CPA after an adequate
post-change window before making another material budget change. Keep the
Consideration campaign paused unless a new assisted-conversion measurement plan
or a materially different test design is approved.

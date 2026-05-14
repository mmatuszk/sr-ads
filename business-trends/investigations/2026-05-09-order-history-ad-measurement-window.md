# Order History and Ad Measurement Window

Date: 2026-05-09

## Scope

This note records the ad-measurement implications from reviewing the local Shopify / Matrixify order export:

`audiences/runs/2026-05-09-performance-max-customer-match/source/Export_2026-05-09_173702.xlsx`

The source export contains customer PII and must remain out of git. This note records only aggregate findings.

The analysis used roughly the last 5 years of valid orders through the export's latest processed order on `2026-05-08`.

## Main conclusion

Silk Resource ad performance should be judged primarily by **conversion value / cost** over a **56-90 day** window.

Short windows can still be useful for diagnostics, but they are too noisy for budget decisions because revenue is highly concentrated in a small number of large orders.

## Order-size distribution

Valid 5-year order set:

- orders: about `3,507`
- customers: about `2,049`
- revenue: about `$1.146M`
- median order value: about `$22`
- mean order value: about `$327`
- 90th percentile order value: about `$863`
- 95th percentile order value: about `$1,719`
- 99th percentile order value: about `$4,700`
- max order value: about `$18,120`

Revenue concentration:

- orders under `$30`: `54%` of orders, `1.6%` of revenue
- orders under `$100`: about `65%` of orders, `3.6%` of revenue
- orders `$300+`: about `20%` of orders, `88%` of revenue
- orders `$1,000+`: about `9%` of orders, `69%` of revenue
- orders `$2,500+`: about `3%` of orders, `41%` of revenue
- orders `$5,000+`: less than `1%` of orders, `20%` of revenue

Top-order concentration:

- top `1%` of orders: about `22%` of revenue
- top `5%` of orders: about `54%` of revenue
- top `10%` of orders: about `72%` of revenue
- top `20%` of orders: about `88%` of revenue

Implication:

Order count and CPA are secondary diagnostics. They can be actively misleading if a period has many sample orders but few large fabric / wallpaper purchases.

## Repeat behavior

5-year customer frequency:

- `1` order customers: about `72%` of customers, `28%` of revenue
- `2-5` order customers: about `24%` of customers, `36%` of revenue
- `6+` order customers: about `3%` of customers, `36%` of revenue

Repeat-purchase timing:

- median time from first to second order: about `10` days
- about `70%` of second orders happen within `30` days
- about `84%` happen within `90` days
- about `90%` happen within `180` days
- about `95%` happen within `1` year

Sample-first customers who later made a real purchase:

- median sample-to-purchase gap: about `18` days
- about `63%` convert within `30` days
- about `83%` convert within `90` days
- about `90%` convert within `180` days
- median later purchase: about `$472`
- average later purchase: about `$977`

Implication:

Most measurable follow-on value appears within `90` days, but a meaningful tail continues to `180` days and some value appears up to a year later.

## Window stability

Rolling-window revenue was very volatile:

- `7` day median revenue: about `$2.8k`; high volatility
- `14` day median revenue: about `$5.4k`; still high volatility
- `28` day median revenue: about `$12.3k`; directionally useful but still noisy
- `56` day median revenue: about `$28.2k`; better for budget reads
- `84-90` day median revenue: about `$41-43k`; best regular operating read

Typical full-month behavior:

- median monthly revenue: about `$13.8k`
- median monthly orders: about `41`
- about `90%` of full months had at least one `$1,000+` order
- about `78%` of full months had at least two `$1,000+` orders

Even a month can be meaningfully affected by whether large orders landed inside or outside the date range.

## Recommended ad-performance cadence

Use the following cadence for paid media evaluation:

| Window | Use |
| --- | --- |
| `7-14` days | Diagnostics only: spend pacing, tracking health, CPC/CPM changes, obvious breakage |
| `28-30` days | Directional read after a known change, but not enough for final budget judgment |
| `56-90` days | Primary budget and ROAS evaluation window |
| `180` days | Strategic cohort / customer quality / sample-to-purchase read |
| `1` year | Long-tail LTV and returning-customer analysis |

## Metric priority

Primary:

- conversion value / cost
- conversion value
- value per click / interaction
- large-order count and share where available

Secondary:

- conversions
- conversion rate
- CPA
- sample-order count

Avoid optimizing primarily for raw conversion count or CPA unless sample orders and low-value purchases are separated from larger purchase behavior.

## Google Ads interpretation

For Google Ads / Performance Max:

- use rolling `90` day conversion value / cost as the main scorecard
- use rolling `28` day trends to detect rapid deterioration or recovery
- do not overreact to one-week or two-week ROAS swings
- treat sample-order conversions as assistive signals, not final value
- evaluate budget changes after at least `28` days, with the real decision made after `56-90` days when possible

## Related knowledge

The shared business-model assumptions are documented in:

- `sr-knowledge/docs/business/order-history-and-ad-measurement.md`

# Max-2 Known-Event Analysis

Date: 2026-07-21

## Question

Could either the April 2026 Shopify pricing incident or the May 2026
Scalamandre catalog upload explain the lower Shopify ROAS observed in the
seasonally matched Max-2 comparison?

The base comparison uses `SR Sales` for WooCommerce and `Google Shopping App
Purchase` for Shopify, excludes the duplicate WooCommerce purchase action, and
excludes October through December 2025. Across 28 matched January-through-July
weeks, WooCommerce ROAS was `3.271` and Shopify ROAS was `2.389`, a Shopify
difference of `-27.0%`.

## Pricing Incident

The weekly sale workflow ran on April 9, 2026. The documented risk was that
mutating Shopify variant `price` and `compare_at_price` could restore a product
from an already-corrupted baseline. The safer discount-code policy was recorded
on April 11.

| Comparison | Matched weeks | Woo ROAS | Shopify ROAS | Shopify difference |
| --- | ---: | ---: | ---: | ---: |
| Base | 28 | 3.271 | 2.389 | -27.0% |
| Exclude Apr 6 and Apr 13 Shopify weeks | 26 | 3.279 | 2.309 | -29.6% |
| Also exclude Apr 20 attribution week | 25 | 3.231 | 1.819 | -43.7% |

Removing the affected window does not improve Shopify's relative result. The
incident may contaminate individual order values, but it does not explain the
lower aggregate Shopify ROAS. The April series is also volatile because a small
number of high-value orders materially affect weekly conversion value.

Google Ads' standard weekly conversion metrics are assigned to the ad
interaction date. Product-level conversion value is attributed to the clicked
product and does not prove that the clicked item was the purchased line item.
For that reason, anomalously high product-attributed values were not treated as
proof of a product pricing error.

## Scalamandre Catalog Expansion

Timeline:

- May 21, 2026 at 16:48 UTC: the production create workbook was generated with
  `2,111` create rows. A May 23 Shopify backup contains `2,132` Scalamandre
  product rows created May 21; they were draft and unpublished in that backup.
- May 28, 2026 at 03:39: a Merchant Center screenshot shows `7,465` total
  products: `7,270` approved, `180` under review, and `15` not approved. The
  status-history chart rises from roughly 5,500 to 7,500 products around this
  date.
- Through July 19, only three products in the imported Shopify ID range appear
  in Max-2 Shopping performance. Together they generated `78` impressions,
  `1` click, `$1.95` cost, and `$0` conversion value.

ROAS around the Merchant Center exposure date:

| Period | Weeks | Cost | Conversion value | ROAS |
| --- | ---: | ---: | ---: | ---: |
| Four complete weeks before | 4 | $8,321.34 | $9,919.43 | 1.192 |
| Event week beginning May 25 | 1 | $2,101.67 | $1,072.76 | 0.510 |
| First four complete weeks after | 4 | $8,966.19 | $11,972.15 | 1.335 |
| Seven complete weeks after | 7 | $15,575.33 | $17,497.30 | 1.123 |

The event week was weak, but the next four complete weeks were stronger than
the four weeks before. The seven-week post period was about 5.8% below the
four-week pre-period. With only `$1.95` of direct spend on matching imported
products, direct budget diversion is negligible. A broader feed-learning or
auction effect cannot be ruled out from these data, but the timing does not show
a sustained immediate deterioration attributable to the upload.

## Native Sample Platform Rollout

The native sample catalog was created on May 30, 2026. Production run
`20260530T044721Z` created `3,034` managed sample products with no errors. The
storefront release tag `sr-20260530-104752` followed at 10:48 Pacific and is the
best recorded time for the native sample-path rollout.

This event did not divert Shopping spend directly. None of the `3,034` native
sample product IDs appears in Max-2 product performance through July 19: `0`
impressions, `0` clicks, and `$0` spend. It can nevertheless change the signals
Google receives from normal web checkout.

| 28-day period | Valid orders | Web orders | Legacy app sample orders | Native sample orders | Native sample-only orders |
| --- | ---: | ---: | ---: | ---: | ---: |
| Before: May 2–29 | 34 | 12 | 21 | 0 | 0 |
| After: May 31–Jun 27 | 147 | 144 | 0 | 105 | 102 |

The old Product Samples app orders were created as `shopify_draft_order`. All
`105` native sample orders in the post period were normal `web` orders. The
median native sample-only subtotal was `$2.99`, and the median order total was
`$8.25`. Moving samples into normal web checkout makes them much more likely to
fire or qualify for Shopify's Google purchase measurement. An ad-acquired user
can therefore generate a low-value primary `Google Shopping App Purchase`
signal even though Google never advertised the sample product itself.

| Metric | 28 days before | 28 days after | Change |
| --- | ---: | ---: | ---: |
| Spend / day | $303.52 | $320.95 | +5.7% |
| Clicks / day | 268.6 | 304.0 | +13.2% |
| CPC | $1.130 | $1.056 | -6.6% |
| CTR | 1.147% | 1.286% | +12.1% |
| Attributed conversions / day | 2.650 | 3.464 | +30.7% |
| Average attributed conversion value | $126.42 | $110.80 | -12.4% |
| ROAS | 1.104 | 1.196 | +8.3% |

The aggregate pattern is consistent with conversion-mix dilution rather than
worse traffic pricing: conversion count rose, average conversion value fell,
CPC fell, and CTR improved. It is not order-level attribution proof because the
Shopify orders and Google conversions are not joined.

Weekly timing does not show a clean immediate negative relationship. The event
week beginning May 25 had only five native sample orders and `0.510` ROAS. The
first four complete post-rollout weeks had `106` native sample orders and
`1.335` ROAS, above the `1.192` four-week pre-period. The next three weeks had
`95` native sample orders and `0.836` ROAS. Across the seven complete post weeks,
contemporaneous native sample volume was positively correlated with ROAS
(`r = +0.44`, `n = 7`), not negatively. A two-week lag produces a negative
correlation (`r = -0.71`) but only five paired observations, so it is a lead for
future testing, not reliable evidence.

Maximize Conversion Value uses the transaction value, not merely conversion
count. The signal problem is therefore that a `$2.99` sample is reported at its
immediate value while its economically important follow-on purchase may arrive
weeks later or outside the 30-day attribution window. This can dilute reported
ROAS and train bidding on values that understate sample-customer lifetime value.

## July Is Worse Than June So Far

July 1–19 should first be compared with June 1–19 because July is incomplete.
On that matched-day basis, Max-2 spent only 2.6% less but produced 31.0% less
Google-attributed conversion value. ROAS fell from `1.038` to `0.735`, a 29.1%
decline.

| Metric | June 1–19 | July 1–19 | Change |
| --- | ---: | ---: | ---: |
| Spend | $6,201.29 | $6,037.67 | -2.6% |
| Conversion value | $6,434.07 | $4,439.60 | -31.0% |
| ROAS | 1.038 | 0.735 | -29.1% |
| Attributed conversions | 62.85 | 50.35 | -19.9% |
| Average conversion value | $102.36 | $88.17 | -13.9% |
| CPC | $1.069 | $1.210 | +13.2% |
| CTR | 1.225% | 1.278% | +4.3% |
| Purchase conversion rate | 1.020% | 0.968% | -5.1% |

Against the full-June daily rate, July looks even weaker: daily spend is almost
identical while ROAS is 46.3% lower (`0.735` versus `1.369`). This larger gap is
partly because several high-value conversions arrived late in June, so the
matched first-19-days comparison is the fairer current read.

The July decline is not an engagement problem: CTR improved. The measurable
pressure is a combination of clicks costing 13.2% more, 19.9% fewer attributed
conversions, and average attributed conversion value falling 13.9%. The
conversion-rate decline itself is modest at 5.1%.

All-channel Shopify activity moved in the opposite direction. Valid orders rose
from `86` to `117`, total order value rose from `$10,970` to `$22,466`, and
non-sample order value rose from `$10,141` to `$20,605` between the matched
periods. Native samples remained about 72% of valid orders in both periods,
although their absolute rate rose from 3.26 to 4.47 per day. This divergence
suggests July's weakness is concentrated in Google attribution, Google traffic,
or channel mix rather than a store-wide sales decline. Shopify and Google orders
are not joined, so it does not identify which sales originated from Max-2.

## Large-Order Variation Can Explain the Short-Term Gap

The historical order analysis confirms that Silk Resource revenue is extremely
concentrated. Across roughly 3,507 valid orders, the median order was about `$22`
while the mean was about `$327`. The top 5% of orders generated about 54% of
revenue, and the top 10% generated about 72%. A historical 95th-percentile order
was approximately `$1,719`.

The Google-attributed value gap between June 1–19 and July 1–19 is only
`$1,994`. If one additional historical 95th-percentile order had been attributed
to July, July ROAS would be `1.020` instead of `0.735`, almost identical to
June's `1.038`. One `$2,000` order would move July ROAS to `1.067`, above June.

The short-window history points in both directions:

- July's 29.1% ROAS decline is not unusual. About 33% of adjacent 19-day
  comparisons in the January–June 2026 baseline declined by at least that much.
- July's absolute `0.735` ROAS is unusually low: it is around the bottom 1–2%
  of rolling 19-day ROAS windows ending by June 30.
- These rolling windows overlap heavily, so the percentile and frequency are
  descriptive volatility checks, not independent statistical significance
  tests.

All-channel Shopify data argues against a store-wide demand collapse. July 1–19
had eight `$1,000+` orders versus four in June 1–19, and total Shopify order
value was about twice as high. The simplest current interpretation is that
large-order timing and which channel received attribution are major contributors
to the Google ROAS swing. The unusually low absolute Google result still merits
monitoring, but a 19-day window is insufficient to diagnose a structural failure.

## Budget Change Checks

Budget changes clearly changed traffic volume, but the available pre/post tests
do not show a stable efficiency penalty caused by budget alone.

| Change | Window | Spend/day | Clicks/day | CPC | ROAS |
| --- | --- | ---: | ---: | ---: | ---: |
| Apr 23: $360 → $285 | 14d post vs pre | -19.7% | -17.9% | -2.2% | -58.6% |
| May 16: $285 → $315 | first 7d post vs pre | +26.8% | +26.2% | +0.5% | -11.7% |
| May 16: $285 → $315 | first 14d post vs pre | +8.9% | +8.1% | +0.8% | +12.3% |

The April ROAS comparison is contaminated by unusually large pre-period orders
and the pricing incident. After the May increase, ROAS reverses direction when
the window extends from seven to fourteen days. The defensible result is that
budget altered scale; these tests do not show that it reliably made clicks more
expensive or caused the ROAS decline.

## Conclusion

The pricing incident and Scalamandre catalog upload do not explain away the
Shopify-versus-WooCommerce ROAS gap. The native sample rollout is a more
credible contributor to **reported** performance because it changed sample
orders from draft orders to normal web purchases and may therefore have changed
Google's primary purchase signals. It did not make traffic immediately more
expensive, and the timing does not yet prove that it caused the later ROAS
decline. The next causal test should separate Google-attributed samples from
regular purchases and attach 30-, 90-, and 180-day downstream value.

## Spend And Impression Efficiency

Shopify produced 85.1% more impressions and 113.0% more clicks than the matched
WooCommerce period, but spend increased 158.3%. Impression relevance does not
look like the primary failure: click-through rate improved 15.1%, click purchase
conversion rate was nearly flat at -0.8%, and conversion value per thousand
impressions improved 1.9%. The traffic was considerably more expensive: cost
per thousand impressions rose 39.6% and cost per click rose 21.3%. Average
attributed conversion value also fell 10.7%.

The owner confirms that Max-2 used the same target ROAS for many years, covering
both the WooCommerce and Shopify comparison periods. The bidding objective is
therefore controlled in the platform comparison and does not explain the lower
Shopify-era reported ROAS. The same target does not hold scale constant: the
campaign can spend differently as its budget, eligible inventory, auction
prices, demand, feed, and observed conversion-value mix change. In 2026, the
documented daily budget moved from `$360` to `$285` on April 23 and then to
`$315` on May 16; the comparable 2025 budget is not documented here.

The additional `$39,351.87` of Shopify-era spend coincided with `$72,077.29` of
additional conversion value, or `1.83` additional value per additional dollar.
This is not a causal marginal-ROAS estimate because the periods are different
years, but it is consistent with diminishing efficiency at the greater scale.
The higher-spend half of the 2026 weeks returned `1.75` ROAS versus `3.14` for
the lower-spend half.

On July 21, Max-2 used Maximize Conversion Value with a target ROAS of `0.6586`
and a `$315/day` budget. The most recent eight complete weeks returned `1.05`
Google-attributed ROAS on `$17,677` spend. That captured revenue alone would
require roughly a 95% contribution margin to cover advertising cost, but it is
not a complete profitability measure for Silk Resource's sample-first funnel.

The owner reports that `11%` of sample customers buy within three weeks and
`25%` buy over their lifetime. The historical order review found a median
sample-to-purchase gap of 17–18 days, a median later purchase near `$508`, and
an average near `$1,169`. On the current rates, 56% of eventual sample
converters buy after the early window. Modeled downstream revenue per acquired
sample customer is therefore roughly `$127` on the median-order basis or `$292`
on the average-order basis. The portion associated with conversions after the
early window is roughly `$71`–`$164` per sample customer before margin.

This means the available Google ROAS does not establish that the `$315/day`
budget is excessive. The decision requires Max-2-attributed sample-customer
acquisition cost and 90–180 day downstream contribution value. Google's
`$950/day` recommended budget still should not be treated as a profitability
recommendation; it only indicates that additional traffic is available.

## Reproducible Sources

- `../data/campaign-performance/2026-07-21/performance-max-2-weekly-adjusted.csv`
- `../data/campaign-performance/2026-07-21/performance-max-2-weekly-products.csv`
- `../data/campaign-performance/2026-07-21/max-2-woo-vs-shopify-analysis.json`
- `../data/campaign-performance/2026-07-21/max-2-spend-efficiency.json`
- `../data/campaign-performance/2026-07-21/max-2-operational-event-windows.json`
- `../scripts/analyze_max_2_woo_vs_shopify.py`
- `../scripts/export_campaign_product_performance.py`
- `../config/reports/max-2-woo-vs-shopify.sql`

Operational Shopify workbooks and run summaries remain outside this repository
under `sr-automation-runtime`; OAuth credentials and API secrets are never
stored here.

# Sample-to-Purchase Conversion by Sample System

Date: 2026-05-29

## Scope

This note records aggregate sample-to-purchase conversion behavior from the local
Shopify / Matrixify order export:

`audiences/runs/2026-05-09-performance-max-customer-match/source/Export_2026-05-09_173702.xlsx`

The source export contains customer PII and must remain out of git. This note
records only aggregate findings.

The analysis uses valid orders through the export's latest processed order on
`2026-05-08`.

## Classification

Sample history spans WooCommerce plus multiple Shopify sample implementations.
The clean way to analyze conversion is to segment sample orders by their order
signatures rather than use one broad low-order-value rule.

Operational sample mechanisms:

| Mechanism | Order signature |
| --- | --- |
| WooCommerce sample swatches | Imported `Matrixify App` orders with line titles such as `SAMPLE SWATCH` or `SAMPLE SWATCH 3x3"` |
| Imported Shopify sample-app history | Imported `Matrixify App` orders with sample shipping lines such as `Ground Samples Shipping`, `Standard Samples Shipping`, `Priority Samples Shipping`, `Sample - ...`, or `Sample – ...` |
| Prior Shopify one-product app | Shopify `web` orders containing the `Product Sample` product / `product-sample` handle |
| Current Product Samples app | `shopify_draft_order` orders tagged `product-samples-app` |

Orders for showroom samples or sample/remnant goods sold as regular products
should not be treated as operational sample orders merely because the title
contains "sample." They are real merchandise orders.

## Method

Conversion is measured from each customer's first sample order in a mechanism to
the first later non-sample purchase above a threshold.

Two later-purchase thresholds are useful:

* `$100+`: captures meaningful follow-on purchases while excluding most sample
  or small add-on orders.
* `$300+`: captures stronger yardage / wallpaper purchase intent.

For fixed-window conversion rates, denominators are horizon-aware. A customer is
eligible for a `90` day conversion rate only if the first sample order is at
least `90` days before the export's latest order date. This matters most for the
current Product Samples app, which only has partial 2026 follow-up in this
export.

## Mechanism Summary

| Mechanism | Sample orders | Sample customers | Sample-first customers | Ever `$100+` | 30d `$100+` | 90d `$100+` | Ever `$300+` | 30d `$300+` | 90d `$300+` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| WooCommerce sample swatches | 138 | 94 | 85 | 21.3% | 8.5% | 11.7% | 14.9% | 7.4% | 9.6% |
| Imported Shopify sample-app history | 454 | 348 | 320 | 18.7% | 12.1% | 15.8% | 14.4% | 7.5% | 11.2% |
| Prior Shopify one-product app | 164 | 142 | 125 | 18.3% | 11.3% | 17.6% | 14.1% | 8.5% | 13.4% |
| Current Product Samples app | 434 | 340 | 315 | 10.0% | 9.1% | 12.0% | 7.6% | 6.8% | 12.0% |

The current Product Samples app has lower "ever" conversion mainly because the
cohort is young. Its observed 30-day and eligible 90-day rates are in the same
general range as prior systems, though the 90-day denominator is still much
smaller.

## Combined Operational Sample Cohort

Across all operational sample systems:

* sample orders: `1,190`
* sample customers: `879`
* sample-first customers: `821`

Later `$100+` purchases:

* ever converted: `134` customers, `15.2%`
* 30-day eligible conversion: `81 / 802`, `10.1%`
* 90-day eligible conversion: `94 / 645`, `14.6%`
* 180-day eligible conversion: `74 / 451`, `16.4%`
* median gap: `17` days
* median later purchase: about `$508`
* average later purchase: about `$1,169`

Later `$300+` purchases:

* ever converted: `101` customers, `11.5%`
* 30-day eligible conversion: `56 / 802`, `7.0%`
* 90-day eligible conversion: `71 / 645`, `11.0%`
* 180-day eligible conversion: `55 / 451`, `12.2%`
* median gap: `18` days
* median later purchase: about `$960`
* average later purchase: about `$1,658`

## Revenue With Prior Sample

Another useful framing is the reverse question: among real non-sample
purchases, how much revenue came from customers who had previously placed an
operational sample order?

For real purchases of `$100+`:

* real purchase revenue: about `$1.240M`
* revenue with any prior sample: about `$262k`, `21.2%`
* orders with any prior sample: `228 / 1,414`, `16.1%`
* median days since nearest prior sample: `21`
* revenue with prior sample within `30` days: about `$162k`, `13.1%`
* revenue with prior sample within `90` days: about `$220k`, `17.8%`
* revenue with prior sample within `180` days: about `$233k`, `18.8%`
* revenue with prior sample within `365` days: about `$245k`, `19.8%`

For real purchases of `$300+`:

* real purchase revenue: about `$1.131M`
* revenue with any prior sample: about `$248k`, `21.9%`
* orders with any prior sample: `155 / 830`, `18.7%`
* median days since nearest prior sample: `20`
* revenue with prior sample within `30` days: about `$155k`, `13.7%`
* revenue with prior sample within `90` days: about `$210k`, `18.6%`
* revenue with prior sample within `180` days: about `$222k`, `19.6%`
* revenue with prior sample within `365` days: about `$234k`, `20.7%`

This means samples are connected to roughly one-fifth of meaningful real-purchase
revenue in the historical export. The `90` day window captures most of the
sample-tied revenue, which aligns with the sample-to-purchase timing analysis.

## Timing and Value

For customers who do convert after a sample order, most measurable value appears
quickly:

* median gap is roughly `17-18` days in the combined cohort
* `30` days captures a large share of the fast converters
* `90` days is the best regular operating window
* `180` days remains useful for strategic cohort reads, but current app data is
  not yet old enough for that horizon

## Interpretation

Samples are economically meaningful assistive conversions. A useful working
range is:

* roughly `10%` of operational sample customers convert to a `$100+` purchase
  within `30` days
* roughly `15%` convert to a `$100+` purchase within `90-180` days when the
  cohort has enough follow-up
* roughly `7-12%` convert to a `$300+` purchase depending on horizon and sample
  system

This supports treating sample orders as high-intent signals, not final value.
Paid media, site UX, and sample operations should evaluate samples as assistive
events that often lead to larger purchases inside a `30-90` day window.

## Related Notes

* `business-trends/investigations/2026-05-09-order-history-ad-measurement-window.md`

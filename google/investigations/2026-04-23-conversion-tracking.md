# Google Conversion Tracking Investigation

Date: 2026-04-23

## Scope

This note records the technical investigation into Google Ads conversion tracking, enhanced conversions, and cart data issues for the Shopify store.

Source export reviewed:

- `google/data/Enhanced conversions diagnostics alerts.csv`

Related systems reviewed:

- Google Ads account diagnostics
- Shopify `Google & YouTube` app settings
- Shopify `Customer events`
- Theme code in `/Users/marcin/prg/sr-theme`
- Live storefront tag output

## Main conclusion

The Shopify to Google Ads conversion setup appears to be working correctly.

The current evidence does **not** support the idea that the recent business performance drop is primarily caused by broken Google conversion tracking.

Purchase tracking and purchase enhanced conversions look healthy.

Most warnings are limited to:

- upper-funnel secondary Shopify events with weak enhanced conversion coverage
- partial cart data coverage on purchase events
- missing COGS in Merchant Center

These are real issues, but they do not look like the main cause of the broader sales slowdown.

## Google Ads findings

Enhanced conversions diagnostics:

- Total enhanced conversion actions: `7`
- Fully optimized: `3`
  - `Google Shopping App Purchase`
  - `Google Shopping App Begin Checkout`
  - `Google Shopping App Add Payment Info`
- Need attention: `4`
  - `Google Shopping App Add To Cart`
  - `Google Shopping App View Item`
  - `Google Shopping App Page View`
  - `Google Shopping App Search`

Coverage observations from diagnostics:

- `Purchase`: `100%` coverage
- `Begin Checkout`: `100%`
- `Add Payment Info`: `100%`
- `View Item`: `1%`
- `Page View`: `2%`
- `Search`: `0%`

Interpretation:

- purchase enhanced conversions are healthy
- warnings are concentrated in upper-funnel events where Google often has limited user data

Consent mode:

- Status: `Web Excellent`

Conversions with cart data:

- Affected conversion action: `Google Shopping App Purchase`
- Recent purchase events missing cart data: `20%`
- Sold products missing COGS: `100%`

Interpretation:

- purchase conversions are firing
- a subset of purchase events is reaching Google without full cart item payload
- this looks more like payload inconsistency on some flows than a broken purchase setup

## Shopify findings

In Shopify `Google & YouTube`:

- Google Ads connected
- Conversion measurement: `On`
- Enhanced conversions: `On`

Mapped events:

- `Checkout completed -> Google Shopping App Purchase`
- `Checkout started -> Google Shopping App Begin Checkout`
- `Added to cart -> Google Shopping App Add To Cart`
- `Page viewed -> Google Shopping App Page View`
- `Product viewed -> Google Shopping App View Item`
- `Search submitted -> Google Shopping App Search`
- `Payment info submitted -> Google Shopping App Add Payment Info`

In Shopify `Settings > Customer events`:

- App pixels present:
  - `Google & YouTube`
  - `Pinterest`
- Custom pixels:
  - none

Interpretation:

- the Shopify migration/setup appears complete
- there is no sign of a missing official Google pixel setup

## Theme and storefront findings

Theme repo reviewed:

- `/Users/marcin/prg/sr-theme`

What was checked:

- Liquid templates
- app embeds
- custom scripts
- Google / GTM / purchase / conversion code paths

Findings:

- no handwritten Google Ads purchase tag found in the theme
- no GTM container found in the theme code
- no duplicate Google purchase tracking found in Shopify custom pixels
- `theme.liquid` contains Shopify header output and Google Merchant widget, but not a custom purchase conversion implementation
- only custom Google-related event code found was for internal calculator interactions, not purchase tracking

Live storefront tag output:

- official Shopify web pixels manager was loading Google identifiers consistent with the official app
- no extra GTM or duplicate Ads purchase tag was found in storefront HTML

Interpretation:

- theme code is unlikely to be the cause of missing cart data
- duplicate purchase tagging from theme or custom pixels appears unlikely

## Likely explanation for warnings

### Enhanced conversions warnings

Likely caused by some events not carrying enough user-provided data, especially in upper-funnel flows.

Possible reasons:

- user consent not granted
- browser/privacy blocking
- shoppers not yet identified during early funnel events
- incomplete address payload on some flows

### Missing cart data on purchase

Likely caused by a subset of purchase events reaching Google without full cart item data.

Possible reasons:

- alternate Shopify checkout/payment flows
- inconsistent payload availability on some purchase completions
- Shopify/Google app event-path variance

This issue does **not** currently look like a theme-code problem.

## Business impact assessment

Technical conclusion:

- Google purchase conversion tracking is functioning
- Google purchase enhanced conversions are functioning
- warnings exist, but they are mostly secondary or partial data-quality issues

Business conclusion:

- these technical issues do not appear sufficient to explain the recent decline in Google, Pinterest, eBay, and Etsy performance
- the broader performance weakness is more consistent with reduced demand, lower conversion efficiency, and/or weaker traffic quality than with broken tracking

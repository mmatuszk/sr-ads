# Max-2 Product Exclusions

## Date

August 2, 2026

## Purpose

Stop Max-2 from advertising products approved for exclusion through the
expanded-attribution product review, while leaving all other product inventory
eligible.

## Source Control at Time of Apply

- Shopify source: `custom.ad_status = exclude`
- Merchant Center translation: `custom_label_1 = exclude`
- Merchant Center supplemental source: `SR Ad Controls` (`10696160670`)
- Approved and verified Merchant offers: `32`

The Merchant label backfill is documented in
`google/changes/2026-08-02-gmc-ad-exclusion-label-backfill.md`.

The API source above was retired on August 6, 2026. The current production
translation is owned solely by `SR Ad Controls Hosted TSV` (`10702577630`),
using the same `custom_label_1 = exclude` contract. The campaign listing-group
gate did not need to change during that source migration.

## Google Ads Change

- Customer: `5626118344`
- Campaign: `Performance Max-2` (`20647427212`)
- Applied with: `google/scripts/apply_max_2_ad_exclusion.py`
- Google Ads validated all `12` operations before apply.

Asset group `Performance Max-2` (`6479076289`):

- Preserved the existing `custom_label_0` subdivision.
- Added a `custom_label_1 = exclude` excluded unit beneath both the
  `showroom samples` and everything-else branches.
- Retained an included everything-else `custom_label_1` unit beneath both
  branches.

Asset group `Performance Max-2 Control` (`6734634322`):

- Replaced the all-products included root with a `custom_label_1` subdivision.
- Added a `custom_label_1 = exclude` excluded unit.
- Retained an included everything-else `custom_label_1` unit.

## Verification

The live post-apply query found:

- Original asset group: `2` exclusion gates and `0` unguarded included leaves.
- Control asset group: `1` exclusion gate and `0` unguarded included leaves.
- Follow-up dry run: `0` changes required.

No campaign status, budget, bidding, creative assets, audience signals, search
themes, final URLs, or Merchant Center product data were changed by the Google
Ads operation.

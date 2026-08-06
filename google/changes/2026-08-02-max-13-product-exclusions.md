# Max-13 Product Exclusions

## Date

August 2, 2026

## Purpose

Apply the shared Shopify and Merchant Center ad-exclusion control to
Performance Max-13 while leaving every other product eligible.

## Google Ads Change

- Customer: `5626118344`
- Campaign: `Performance Max-13` (`23453016844`)
- Asset group: `Performance Max-13` (`6657971628`)
- Source control: `custom_label_1 = exclude`
- Applied with: `google/scripts/apply_max_13_ad_exclusion.py`
- Google Ads validated all `4` operations before apply.

The original all-products included root was replaced with a
`custom_label_1` subdivision containing:

- `exclude`: excluded
- Everything else in Custom label 1: included

## Verification

The live post-apply query found one exclusion gate and zero unguarded included
leaves. A follow-up dry run reported zero changes required.

No campaign status, budget, bidding, creative assets, audience signals, search
themes, final URLs, or Merchant Center product data were changed.

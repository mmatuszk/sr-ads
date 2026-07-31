# SR Google Automation And Merchant API Access

## Date

July 30, 2026

## Reason

The existing Google Cloud project had grown beyond Gemini Gem publishing. It
already supported shared Drive, Sheets, and Google Ads workflows and now needs
Merchant Center access for product-segmentation analysis and a future
Shopify-to-Merchant supplemental label sync.

## Changes

- Changed the Google Cloud project display name from
  `SR Gem Knowledge Publisher` to `SR Google Automation`.
- Preserved the immutable project ID `sr-gem-knowledge-publisher` and project
  number `997426528564`.
- Enabled Cloud Resource Manager API.
- Enabled Merchant API.
- Reauthorized shared local ADC with Cloud, Drive, Sheets, Google Ads, and
  Merchant scopes.
- Registered the Cloud project with Silkresource Merchant Center account
  `524184721`.
- Registered and verified the existing SR Google user as an API developer
  contact.
- Added the canonical access runbook at
  `sr-knowledge/docs/technical/google-automation-access.md`.

## Verification

- Confirmed all five OAuth scopes in the refreshed ADC token.
- Confirmed Merchant API account access for `Silkresource`.
- Listed Merchant Center data sources without mutation.
- Identified `Shopify App API` data source `10580915723` as the primary Shopify
  source.
- Confirmed its content language is `en`, feed label is
  `USD_94580244785`, and its default rule currently takes attributes only from
  itself.
- Read a small sample of processed products and confirmed Shopify offer IDs use
  the pattern `shopify_ZZ_{shopify_product_id}_{shopify_variant_id}`.
- No Merchant Center products, data sources, default rules, labels, campaigns,
  or bids were changed.

## Next Step

Define and approve the Shopify segmentation metafields and the mapping to
Merchant Center `custom_label_0` through `custom_label_4` before creating a
supplemental API data source.


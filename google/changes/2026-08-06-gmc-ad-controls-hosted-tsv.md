# GMC Ad Controls Hosted TSV

## Decision

Replace ongoing Merchant API product writes with one complete supplemental TSV
hosted by Pine. Shopify remains the source of truth for `custom.ad_status`.

| Shopify state | TSV `custom_label_1` |
| --- | --- |
| `exclude` | `exclude` |
| blank or `active` | `active` |
| Not published to Google | No row |

## Runtime Contract

- Hosted URL:
  `https://pine.silkresource.com/mm-automation/feeds/gmc-ad-controls.tsv`
- Pine path:
  `/home/marcin/sr-automation-runtime/feeds/gmc-ad-controls.tsv`
- Delivery: Merchant Center scheduled HTTPS fetch with Basic authentication
- Writers: the SR Automation webhook worker and attended full-feed generator
- Pine Google credential: none

The same generator is used for webhooks and bulk work. A local attended run can
upload the complete TSV and metadata atomically to Pine over SSH. Merchant API
product writes and immediate-fetch triggers are not part of the routine path.

## Production Migration

Completed August 6, 2026:

- Created `SR Ad Controls Hosted TSV` (`10702577630`) and linked it to Shopify
  primary source `10580915723`.
- Processed 4,030 TSV rows; 4,029 matched current Merchant offers. The one
  unmatched row was explicit `active` offer
  `shopify_ZZ_10412760269105_51896422957361`.
- Reduced the primary rule to the hosted source followed by the Shopify source.
- Deleted historical API source `10696160670`.
- Verified all 32 exclusion offers after deletion and verified a 20-offer
  active sample.
- Enabled the SR Automation webhook dispatcher and hosted-feed updater in apply
  mode.
- Sent the signed standing test-product webhook through the production receiver
  and queue. The combined product job and dedicated GMC job both completed;
  every product step was unchanged and feed checksum
  `59cf9c2639f0427176aa936acb1beb624f8f3d3b7a86c735833291a4ebf87221`
  remained unchanged.

Only source `10702577630` now owns `custom_label_1`.

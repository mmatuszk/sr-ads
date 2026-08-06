# GMC Ad-Exclusion Label Backfill

## Date

August 2, 2026

## Purpose

Exclude the 32 products approved through the expanded-attribution product
review from applicable Google Ads campaigns without replacing the Shopify
Merchant Center product source.

## Approved Change

- Merchant account: `524184721` (`Silkresource`)
- Shopify primary data source: `10580915723` (`Shopify App API`)
- Create supplemental API source: `SR Ad Controls`
- Preserve the Shopify primary source's complete default rule and append the
  supplemental source reference.
- Submit `custom_label_1 = exclude` for the 32 canonical Merchant offer IDs in
  the approved `Expanded Exclude` report sheet.
- Do not change price, availability, inventory, publication, destinations,
  campaigns, bids, or the Shopify primary product inputs.

## Dry-Run Verification

- Approved Shopify products: `32`
- Unique report Google item IDs: `32`
- Unique canonical Merchant offer IDs: `32`
- Existing `custom_label_1` values: all blank
- Planned label changes: `32`
- Conflicting label values: `0`
- Planned supplemental-source action: create
- Planned Shopify default-rule action: preserve and link

Dry-run audit:

```text
~/sr-automation-runtime/output/gmc-ad-exclusion-backfill/gmc-ad-exclusion-backfill-dry-run-20260802T214837748735Z.json
```

## Apply Verification

Applied through the guarded SR Automation workflow.

- Created supplemental source `SR Ad Controls`: `10696160670`
- Preserved and linked Shopify primary source `10580915723`
- Submitted only `custom_label_1 = exclude`
- Verified processed offers with `exclude`: `32/32`
- Follow-up dry-run label changes: `0`
- Follow-up dry-run unchanged offers: `32`

Merchant processing exceeded the initial short verification window, so the
idempotent command was rerun after partial processing. The final apply changed
the remaining 8 offers, preserved 24 already-processed offers, and verified all
32. The verifier now allows the documented several-minute Merchant processing
window.

Final apply audit:

```text
~/sr-automation-runtime/output/gmc-ad-exclusion-backfill/gmc-ad-exclusion-backfill-apply-20260802T215313979141Z.json
```

Final zero-change dry-run audit:

```text
~/sr-automation-runtime/output/gmc-ad-exclusion-backfill/gmc-ad-exclusion-backfill-dry-run-20260802T215327063065Z.json
```

## Historical Status

This API source was a migration predecessor. It was unlinked and deleted on
August 6, 2026 after `SR Ad Controls Hosted TSV` (`10702577630`) processed and
verified successfully. Do not recreate source `10696160670` or use this
historical API backfill for current synchronization. Shopify metafields and the
complete hosted TSV are now the only production path for `custom_label_1`.

# Google

This folder is for Google Ads and Google conversion tracking work.

## Structure

- `data/` raw exports and source files
- `scripts/` Google Ads API reporting and management commands
- `config/` reporting definitions and operational guardrails when introduced
- `investigations/` dated technical and performance reviews
- `changes/` dated campaign and budget change logs

Keep all Google-specific API calls in this folder. New commands should default
to read-only behavior. Commands that change live campaigns must use explicit
operator confirmation, channel guardrails, and a dated record in `changes/`.

Shared audience generation and run notes live in `../audiences/` because the same customer lists can support Google, Pinterest, and future advertising platforms.

## API Authentication

Google Ads uses the same user-based Application Default Credentials (ADC)
pattern as the existing SR Google Drive integration. OAuth credentials stay in
the standard local ADC file and are loaded by the Google client library; they
are not committed to this repository.

The OAuth grant must include the existing Drive and Sheets scopes plus:

```text
https://www.googleapis.com/auth/adwords
```

Use the SR Workspace-approved OAuth client stored outside Git at:

```text
~/.config/sr-gem-drive/oauth-client.json
```

Create or refresh local ADC with all required scopes:

```bash
gcloud auth application-default login \
  --client-id-file "$HOME/.config/sr-gem-drive/oauth-client.json" \
  --scopes "https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/adwords"
```

Google Ads also requires a developer token created in a Google Ads manager
account. Store the token and account IDs outside Git in:

```text
~/.config/sr-ads/google_ads.json
```

Restrict that file to the local user with mode `600`. Its expected shape is:

```json
{
  "developer_token": "REDACTED",
  "login_customer_id": "4422175447",
  "customer_id": "5626118344"
}
```

Account roles:

- `4422175447` is the Silk Resource Ads Manager account. It owns the developer
  token and is the `login_customer_id` for manager-routed calls.
- `5626118344` is the linked operating account that contains the campaigns and
  is the `customer_id` for normal reporting and management calls.
- The OAuth user also has direct access to the operating account, so direct
  calls are available as a diagnostic fallback.

The Google Cloud OAuth project is `sr-gem-knowledge-publisher`, where the Google
Ads API must remain enabled.

## Verify API Access

From the repository root, run the read-only verifier:

```bash
.venv/bin/python google/scripts/verify_google_ads_access.py
```

The normal path sends the manager account as `login_customer_id` and queries the
linked operating account. To test the OAuth user's direct account access without
the manager header, run:

```bash
.venv/bin/python google/scripts/verify_google_ads_access.py --direct
```

Both paths were verified successfully on July 16, 2026. The verifier reads
account metadata and campaign names/statuses only; it does not mutate Google Ads.

## Export Weekly Campaign Performance

Export the last `104` complete Monday-through-Sunday weeks for `Performance
Max-2` (campaign ID `20647427212`):

```bash
.venv/bin/python google/scripts/export_campaign_weekly_performance.py
```

The exporter excludes the current partial week and writes a campaign-level CSV,
a conversion-action detail CSV, and retrieval metadata under the dated
`google/data/campaign-performance/` folder. It is read-only. Use
`--campaign-id`, `--weeks`, or `--output-dir` to override the defaults.

For the Max-2 analysis, keep `SR Sales` and exclude the duplicate legacy
WooCommerce purchase action from the adjusted series:

```bash
.venv/bin/python google/scripts/export_campaign_weekly_performance.py \
  --exclude-conversion-action-name '[85ed] Google for WooCommerce purchase action'
```

This preserves the raw reported campaign and conversion-action files and adds a
`weekly-adjusted.csv` file. The metadata records the exclusion and method.

Review conversion-action detail before interpreting long-range ROAS. Historical
tracking migrations can leave more than one value-bearing purchase action active
in the same week and inflate Google Ads' reported conversion value. The export
metadata identifies weeks with such overlaps; raw values are not silently
adjusted.

## Compare WooCommerce And Shopify ROAS

Run the seasonally matched Max-2 comparison after exporting the weekly data:

```bash
python3 google/scripts/analyze_max_2_woo_vs_shopify.py
```

The analysis uses `SR Sales` for WooCommerce and `Google Shopping App Purchase`
for Shopify. It excludes the duplicate legacy WooCommerce purchase action and
October through December 2025, when the Shopify store was not fully set up. The
comparison aligns `28` complete January-through-July weeks in 2025 and 2026.

The reproducible reconciliation query is:

```text
google/config/reports/max-2-woo-vs-shopify.sql
```

Export weekly product-level Shopping performance when investigating feed or
catalog events:

```bash
.venv/bin/python google/scripts/export_campaign_product_performance.py
```

The default export covers Max-2 from January 5 through July 19, 2026 and writes
product attributes, impressions, clicks, cost, conversions, and conversion
value to the dated campaign-performance folder. The export is read-only and can
be large; the July 21 run contains `101,214` product-week rows.

The generated `performance-max-2-weekly-products.csv` is intentionally ignored
by Git because it is large and reproducible from the Google Ads API. Its small
metadata JSON remains tracked. To reproduce the July 21 analysis input exactly,
first complete the OAuth and developer-token setup above, then run from the
repository root:

```bash
.venv/bin/python google/scripts/export_campaign_product_performance.py \
  --start-date 2026-01-05 \
  --end-date 2026-07-19 \
  --output-dir google/data/campaign-performance/2026-07-21
```

Use the same command before rerunning
`google/scripts/analyze_max_2_woo_vs_shopify.py` in a fresh checkout. Override
the dates and output directory when creating a new dated analysis snapshot.

The pricing-error and Scalamandre catalog-event review is documented in:

```text
google/investigations/2026-07-21-max-2-known-event-analysis.md
```

### Developer Token Normalization Gotcha

Treat the developer token as an opaque string. A valid token can contain
punctuation such as hyphens or underscores. Never remove, replace, change case,
or otherwise normalize its characters.

Google Ads customer IDs are different: UI-formatted customer IDs may have
hyphens removed before API use. Normalize only `login_customer_id` and
`customer_id`, never `developer_token`.

Removing a hyphen from the developer token caused
`AuthenticationError.DEVELOPER_TOKEN_INVALID` even though the token copied from
the API Center was correct. Preserve the token exactly as issued.

## Measurement Notes

- Use conversion value / cost as the primary Google Ads performance metric.
- Treat `7-14` day windows as diagnostics only.
- Use `28-30` days for directional reads after known changes.
- Use `56-90` days as the main budget and ROAS evaluation window.

Source rationale:

- `../business-trends/investigations/2026-05-09-order-history-ad-measurement-window.md`

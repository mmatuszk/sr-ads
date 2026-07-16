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

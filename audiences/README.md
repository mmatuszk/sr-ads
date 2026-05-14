# Audiences

This folder tracks reusable paid-media audience strategy, aggregate run summaries, and generation logic across Google, Pinterest, and future advertising platforms.

Raw customer exports and generated Customer Match upload/review files contain customer PII and must stay out of git, even in this private repo. Store those sensitive artifacts locally or in the restricted Google Drive folder for this project.

Track:

- audience methodology
- run notes and decision records
- workflow config and named audience presets
- scripts that regenerate upload files from source exports
- aggregate summary JSON files

Do not track:

- source exports used for a dated run
- generated audience workbooks or CSVs containing customer identifiers

Use dated run folders:

```text
audiences/runs/YYYY-MM-DD-short-description/
  source/
  output/
```

Sensitive cross-computer artifacts for this project should be stored in the restricted Google Drive folder:

```text
https://drive.google.com/drive/folders/1Q1IQo3dV0vtZTIwP52Ovpjh6WYawUKIr
```

## Google Customer Match Builder

The reusable builder and config are:

```text
audiences/scripts/build_customer_match.py
audiences/config/customer_match/workflow.yaml
```

Recommended preset-based run:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

.venv/bin/python audiences/scripts/build_customer_match.py \
  --run audiences/runs/2026-05-09-performance-max-customer-match \
  --preset lifetime_1k_recent_100 \
  --exclude-email owner@example.com
```

The builder resolves input and output paths from the run directory:

- input: latest matching source export under `source/`
- review workbook: `output/customer_match_YYYY-MM-DD_PRESET.xlsx`
- review CSV: `output/customer_match_YYYY-MM-DD_PRESET.csv`
- Google Ads upload CSV: `output/customer_match_YYYY-MM-DD_PRESET.google_upload.csv`
- Pinterest Ads upload CSV: `output/customer_match_YYYY-MM-DD_PRESET.pinterest_upload.csv`
- summary JSON: `output/customer_match_YYYY-MM-DD_PRESET.summary.json`

Use `baseline` for the default high-signal audience. Other named presets live in `audiences/config/customer_match/workflow.yaml`.

Use `pinterest_seed` for Pinterest customer-list uploads and actalike source audiences. It keeps buyer-quality rules but widens the window to five years so Pinterest has enough rows after matching.

Direct path and threshold flags are still supported for one-off checks, but repeatable business rules should be captured as named presets.

The review workbook and review CSV are for operator review only:

- `email`
- `reason`

The platform upload files are intentionally separate:

- Google Ads: single `Email` header column
- Pinterest Ads: one email per row with no header

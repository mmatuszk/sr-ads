# Google Audiences

This folder tracks reusable Google Ads audience strategy, aggregate run summaries, and generation logic.

Raw customer exports and generated Customer Match upload/review files contain customer PII and must stay out of git, even in this private repo. Store those sensitive artifacts locally or in the restricted Google Drive folder for this project.

Track:

- audience methodology
- run notes and decision records
- scripts that regenerate upload files from source exports
- aggregate summary JSON files

Do not track:

- source exports used for a dated run
- generated audience workbooks or CSVs containing customer identifiers

Use dated run folders:

```text
google/audiences/runs/YYYY-MM-DD-short-description/
  source/
  output/
```

Sensitive cross-computer artifacts for this project should be stored in the restricted Google Drive folder:

```text
https://drive.google.com/drive/folders/1Q1IQo3dV0vtZTIwP52Ovpjh6WYawUKIr
```

## Customer Match Builder

The reusable builder is:

```text
google/audiences/scripts/build_customer_match.py
```

Example:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

.venv/bin/python google/audiences/scripts/build_customer_match.py \
  --input /Users/marcin/Downloads/Export_2026-05-09_173702.xlsx \
  --output google/audiences/runs/2026-05-09-performance-max-customer-match/output/customer_match_2026-05-09.xlsx \
  --csv-output google/audiences/runs/2026-05-09-performance-max-customer-match/output/customer_match_2026-05-09.csv \
  --summary-output google/audiences/runs/2026-05-09-performance-max-customer-match/output/customer_match_2026-05-09.summary.json \
  --exclude-email marcin201@gmail.com
```

The output workbook has the upload-review format used for the Performance Max Customer Match list:

- `email`
- `reason`

# Google Audiences

This folder tracks reusable Google Ads audience strategy, source exports, generated audience data, and generation logic.

Because this is a private repo, dated audience runs may include the source export and generated upload/review files needed to reproduce a decision.

Track:

- audience methodology
- run notes and decision records
- scripts that regenerate upload files from source exports
- source exports used for a dated run
- generated audience workbooks, CSVs, and summary JSON files

Use dated run folders:

```text
google/audiences/runs/YYYY-MM-DD-short-description/
  source/
  output/
```

## Customer Match Builder

The reusable builder is:

```text
google/audiences/scripts/build_customer_match.py
```

Example:

```bash
python3 google/audiences/scripts/build_customer_match.py \
  --input /Users/marcin/Downloads/Export_2026-05-09_173702.xlsx \
  --output google/audiences/runs/2026-05-09-performance-max-customer-match/output/customer_match_2026-05-09.xlsx \
  --csv-output google/audiences/runs/2026-05-09-performance-max-customer-match/output/customer_match_2026-05-09.csv \
  --summary-output google/audiences/runs/2026-05-09-performance-max-customer-match/output/customer_match_2026-05-09.summary.json \
  --exclude-email marcin201@gmail.com
```

The output workbook has the upload-review format used for the Performance Max Customer Match list:

- `email`
- `reason`

# Performance Max Customer Match Selection

Date: 2026-05-09

## Scope

This note records the customer selection logic used to create a Google Performance Max Customer Match seed list from the Shopify order export:

- `/Users/marcin/Downloads/Export_2026-05-09_173702.xlsx`

The repo keeps only methodology and aggregate summaries. The exact source export and generated Customer Match files for this run contain customer PII, so they are intentionally ignored by git and stored locally or in the restricted Google Drive folder:

- `https://drive.google.com/drive/folders/1Q1IQo3dV0vtZTIwP52Ovpjh6WYawUKIr`

## Business Context

Prior Google Ads review found that Shopify to Google Ads purchase tracking and enhanced conversions were working correctly. The recent performance weakness looked broader than a single tracking issue, with signs of softer demand and lower conversion efficiency across Google, Pinterest, eBay, and Etsy.

For that reason, this audience work is not treated as a tracking fix. It is intended to give Performance Max stronger first-party customer signals, especially around high-value and repeat Silk Resource buyers.

## Source Data

Workbook reviewed:

- Sheet: `Orders`
- Rows: `29,554`
- Columns: `204`
- Top-level order rows: `3,973`
- Latest processed order: `2026-05-08 19:50:30`

The export includes older imported orders going back to 2009 and recent orders through 2026.

## Selection Window

Customer activity was evaluated over the trailing three years from the latest processed order using inclusive calendar dates:

- Start: `2023-05-09`
- End: `2026-05-08`

## Base Filters

Orders were eligible only when they met all of these conditions:

- valid email address present
- not a known internal/test email
- processed inside the trailing three-year window
- not canceled
- payment status not `voided`
- net order total greater than `$0`

Line-item rows were used only to classify product interest. Customer spend and order count were calculated from top-level order rows to avoid double-counting multi-line orders.

## Inclusion Rules

A customer was included when any of these were true:

- recent spend of at least `$250`
- at least `2` recent orders
- single recent order of at least `$500`
- customer had the `designer-program` tag
- Shopify lifetime spend of at least `$3,000` and recent spend of at least `$100`

Reasons in the output identify the qualifying behavior and useful PMax signal context, such as:

- recent spend
- repeat buyer status
- lifetime value
- fabric buyer
- wallpaper buyer
- trim buyer
- pillow buyer
- Scalamandre/design-house interest
- last order date

## Results

From the eligible recent data:

- valid recent orders: `2,985`
- valid recent customers: `1,798`
- selected customers: `689`
- selected recent orders: `1,876`
- selected recent spend represented: `$867,243.87`

## Interpretation

This list is a high-signal seed list for Performance Max, not a narrow targeting list. Performance Max can still serve outside the list, so the purpose is to teach Google what strong Silk Resource customers look like:

- repeat buyers
- premium fabric buyers
- design-house/Scalamandre buyers
- wallpaper and trim buyers
- high-lifetime-value customers

This list is appropriate for:

- Performance Max audience signals
- Customer Match seed data
- new-customer acquisition calibration, if existing customers are also uploaded as an existing-customer definition

## Reproduction

Use the tracked builder:

```bash
python3 google/audiences/scripts/build_customer_match.py \
  --input google/audiences/runs/2026-05-09-performance-max-customer-match/source/Export_2026-05-09_173702.xlsx \
  --output google/audiences/runs/2026-05-09-performance-max-customer-match/output/customer_match_2026-05-09.xlsx \
  --csv-output google/audiences/runs/2026-05-09-performance-max-customer-match/output/customer_match_2026-05-09.csv \
  --summary-output google/audiences/runs/2026-05-09-performance-max-customer-match/output/customer_match_2026-05-09.summary.json \
  --exclude-email marcin201@gmail.com
```

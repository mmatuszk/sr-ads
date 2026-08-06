# Max-2 and Max-13 Target ROAS to 80%

## Requested change

Set the target ROAS for both enabled Performance Max campaigns to `80%`:

| Campaign | ID | Before | Requested |
| --- | --- | ---: | ---: |
| Performance Max-2 | `20647427212` | `65.85798037855759%` | `80%` |
| Performance Max-13 | `23453016844` | `65%` | `80%` |

Both campaigns were verified as enabled, `PERFORMANCE_MAX`, and using
`MAXIMIZE_CONVERSION_VALUE` before the mutation.

## Guarded command

```bash
.venv/bin/python google/scripts/set_max_campaign_target_roas.py \
  --target-roas-percent 80 \
  --apply \
  --confirm-customer-id 5626118344 \
  --confirm-campaign-id 20647427212 \
  --confirm-campaign-id 23453016844 \
  --confirm-target-roas-percent 80
```

## Verification

Applied successfully on August 6, 2026. The Google Ads API returned two
campaign update results. A fresh query immediately after the mutation returned:

| Campaign | ID | Verified target ROAS |
| --- | --- | ---: |
| Performance Max-2 | `20647427212` | `80%` |
| Performance Max-13 | `23453016844` | `80%` |

A subsequent dry run reported both campaigns as unchanged.

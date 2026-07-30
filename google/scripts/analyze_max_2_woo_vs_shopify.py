#!/usr/bin/env python3
"""Compare seasonally matched Max-2 ROAS under WooCommerce and Shopify."""

from __future__ import annotations

import argparse
import calendar
import csv
import json
import math
import random
import re
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


WOO_ACTION = "SR Sales"
SHOPIFY_ACTION = "Google Shopping App Purchase"
WOO_START = "2025-01-06"
WOO_END = "2025-07-20"
SHOPIFY_START = "2026-01-05"
SHOPIFY_END = "2026-07-19"
BOOTSTRAP_SEED = 20260721
BOOTSTRAP_SAMPLES = 20_000
PRICING_INCIDENT_WEEKS = ["2026-04-06", "2026-04-13"]
PRICING_CONSERVATIVE_WEEKS = [*PRICING_INCIDENT_WEEKS, "2026-04-20"]
SCALAMANDRE_PRODUCT_ID_MIN = 10678237462833
SCALAMANDRE_PRODUCT_ID_MAX = 10678639395121


def latest_input_dir(root: Path) -> Path:
    candidates = sorted(path for path in root.iterdir() if path.is_dir())
    if not candidates:
        raise SystemExit(f"No dated campaign exports found under {root}")
    return candidates[-1]


def load_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as input_file:
            return list(csv.DictReader(input_file))
    except FileNotFoundError as exc:
        raise SystemExit(f"Required input not found: {path}") from exc


def quantile(sorted_values: list[float], probability: float) -> float:
    index = min(len(sorted_values) - 1, int(probability * len(sorted_values)))
    return sorted_values[index]


def aggregate(rows: list[dict[str, float | int | str]]) -> dict[str, float | int]:
    totals = {
        key: sum(float(row[key]) for row in rows)
        for key in (
            "cost",
            "conversions",
            "conversion_value",
            "impressions",
            "clicks",
            "interactions",
        )
    }
    return {
        "weeks": len(rows),
        **totals,
        "roas": totals["conversion_value"] / totals["cost"],
        "ctr": totals["clicks"] / totals["impressions"],
        "average_cpc": totals["cost"] / totals["clicks"],
        "conversion_rate": totals["conversions"] / totals["interactions"],
        "average_conversion_value": totals["conversion_value"]
        / totals["conversions"],
        "median_weekly_roas": statistics.median(float(row["roas"]) for row in rows),
    }


def percent_change(current: float, baseline: float) -> float:
    return current / baseline - 1


def paired_exclusion_summary(
    rows: list[dict[str, object]], excluded_shopify_weeks: list[str]
) -> dict[str, object]:
    included = [
        row
        for row in rows
        if str(row["shopify_week_start"]) not in excluded_shopify_weeks
    ]
    woo_roas = sum(float(row["woo_conversion_value"]) for row in included) / sum(
        float(row["woo_cost"]) for row in included
    )
    shopify_roas = sum(
        float(row["shopify_conversion_value"]) for row in included
    ) / sum(float(row["shopify_cost"]) for row in included)
    return {
        "excluded_shopify_weeks": excluded_shopify_weeks,
        "included_paired_weeks": len(included),
        "woo_roas": woo_roas,
        "shopify_roas": shopify_roas,
        "shopify_vs_woo_roas_change": shopify_roas / woo_roas - 1,
    }


def scalamandre_event_summary(input_dir: Path) -> dict[str, object]:
    product_rows = load_csv(input_dir / "performance-max-2-weekly-products.csv")
    matched: list[dict[str, str]] = []
    for row in product_rows:
        match = re.match(r"shopify_zz_(\d+)_", row["product_item_id"])
        product_id = int(match.group(1)) if match else 0
        if SCALAMANDRE_PRODUCT_ID_MIN <= product_id <= SCALAMANDRE_PRODUCT_ID_MAX:
            matched.append(row)

    campaign_rows = load_csv(input_dir / "performance-max-2-weekly-campaign.csv")
    action_rows = load_csv(
        input_dir / "performance-max-2-weekly-conversion-actions.csv"
    )
    campaign_by_week = {row["week_start"]: row for row in campaign_rows}
    action_by_week = {
        row["week_start"]: row
        for row in action_rows
        if row["conversion_action_name"] == SHOPIFY_ACTION
    }

    def window_summary(weeks: list[str]) -> dict[str, object]:
        cost = sum(float(campaign_by_week[week]["cost"]) for week in weeks)
        value = sum(float(action_by_week[week]["conversion_value"]) for week in weeks)
        conversions = sum(float(action_by_week[week]["conversions"]) for week in weeks)
        return {
            "weeks": weeks,
            "cost": cost,
            "conversion_value": value,
            "conversions": conversions,
            "roas": value / cost,
        }

    return {
        "shopify_upload": {
            "production_workbook_generated_at_utc": "2026-05-21T16:48:37Z",
            "production_create_rows": 2111,
            "shopify_created_product_rows_on_2026_05_21": 2132,
            "shopify_status_in_2026_05_23_backup": "Draft and unpublished",
            "product_id_min": SCALAMANDRE_PRODUCT_ID_MIN,
            "product_id_max": SCALAMANDRE_PRODUCT_ID_MAX,
        },
        "merchant_center_exposure": {
            "observed_at": "2026-05-28T03:39:00",
            "total_products": 7465,
            "approved": 7270,
            "under_review": 180,
            "not_approved": 15,
            "limited": 0,
            "evidence": "User-provided Google Merchant Center status-history screenshot",
        },
        "max_2_direct_performance_through_2026_07_19": {
            "distinct_products": len({row["product_item_id"] for row in matched}),
            "impressions": sum(int(row["impressions"]) for row in matched),
            "clicks": sum(int(row["clicks"]) for row in matched),
            "cost": sum(float(row["cost"]) for row in matched),
            "conversion_value": sum(float(row["conversion_value"]) for row in matched),
        },
        "pre_post_roas": {
            "pre_4_complete_weeks": window_summary(
                ["2026-04-27", "2026-05-04", "2026-05-11", "2026-05-18"]
            ),
            "event_week": window_summary(["2026-05-25"]),
            "post_4_complete_weeks": window_summary(
                ["2026-06-01", "2026-06-08", "2026-06-15", "2026-06-22"]
            ),
            "post_7_complete_weeks": window_summary(
                [
                    "2026-06-01",
                    "2026-06-08",
                    "2026-06-15",
                    "2026-06-22",
                    "2026-06-29",
                    "2026-07-06",
                    "2026-07-13",
                ]
            ),
        },
    }


def rolling_roas(rows: list[dict[str, float | int | str]], index: int) -> float | None:
    if index < 3:
        return None
    window = rows[index - 3 : index + 1]
    return sum(float(row["conversion_value"]) for row in window) / sum(
        float(row["cost"]) for row in window
    )


def run_analysis(input_dir: Path) -> dict[str, object]:
    campaign_rows = load_csv(input_dir / "performance-max-2-weekly-campaign.csv")
    action_rows = load_csv(
        input_dir / "performance-max-2-weekly-conversion-actions.csv"
    )
    campaign_by_week = {row["week_start"]: row for row in campaign_rows}
    action_by_week: dict[tuple[str, str], tuple[float, float]] = defaultdict(
        lambda: (0.0, 0.0)
    )
    for row in action_rows:
        key = (row["week_start"], row["conversion_action_name"])
        conversions, value = action_by_week[key]
        action_by_week[key] = (
            conversions + float(row["conversions"]),
            value + float(row["conversion_value"]),
        )

    period_definitions = {
        "WooCommerce": (WOO_START, WOO_END, WOO_ACTION),
        "Shopify": (SHOPIFY_START, SHOPIFY_END, SHOPIFY_ACTION),
    }
    series: dict[str, list[dict[str, float | int | str]]] = {}
    for platform, (start_date, end_date, action_name) in period_definitions.items():
        rows: list[dict[str, float | int | str]] = []
        for week_start, campaign in sorted(campaign_by_week.items()):
            week_end = campaign["week_end"]
            if week_start < start_date or week_end > end_date:
                continue
            conversions, conversion_value = action_by_week[
                (week_start, action_name)
            ]
            cost = float(campaign["cost"])
            rows.append(
                {
                    "week_start": week_start,
                    "week_end": week_end,
                    "platform": platform,
                    "purchase_action": action_name,
                    "cost": cost,
                    "conversions": conversions,
                    "conversion_value": conversion_value,
                    "roas": conversion_value / cost if cost else math.nan,
                    "impressions": int(campaign["impressions"]),
                    "clicks": int(campaign["clicks"]),
                    "interactions": int(campaign["interactions"]),
                }
            )
        if len(rows) != 28:
            raise SystemExit(
                f"Expected 28 complete {platform} weeks, found {len(rows)}"
            )
        series[platform] = rows

    woo_rows = series["WooCommerce"]
    shopify_rows = series["Shopify"]
    woo_summary = aggregate(woo_rows)
    shopify_summary = aggregate(shopify_rows)

    comparisons = {
        "roas": percent_change(
            float(shopify_summary["roas"]), float(woo_summary["roas"])
        ),
        "cost": percent_change(
            float(shopify_summary["cost"]), float(woo_summary["cost"])
        ),
        "conversion_value": percent_change(
            float(shopify_summary["conversion_value"]),
            float(woo_summary["conversion_value"]),
        ),
        "conversions": percent_change(
            float(shopify_summary["conversions"]),
            float(woo_summary["conversions"]),
        ),
        "average_cpc": percent_change(
            float(shopify_summary["average_cpc"]),
            float(woo_summary["average_cpc"]),
        ),
        "conversion_rate": percent_change(
            float(shopify_summary["conversion_rate"]),
            float(woo_summary["conversion_rate"]),
        ),
        "average_conversion_value": percent_change(
            float(shopify_summary["average_conversion_value"]),
            float(woo_summary["average_conversion_value"]),
        ),
    }

    comparison_weeks: list[dict[str, object]] = []
    for index, (woo, shopify) in enumerate(zip(woo_rows, shopify_rows), start=1):
        comparison_weeks.append(
            {
                "season_week": index,
                "woo_week_start": woo["week_start"],
                "shopify_week_start": shopify["week_start"],
                "woo_roas": woo["roas"],
                "shopify_roas": shopify["roas"],
                "woo_rolling_4_week_roas": rolling_roas(woo_rows, index - 1),
                "shopify_rolling_4_week_roas": rolling_roas(
                    shopify_rows, index - 1
                ),
                "woo_cost": woo["cost"],
                "shopify_cost": shopify["cost"],
                "woo_conversion_value": woo["conversion_value"],
                "shopify_conversion_value": shopify["conversion_value"],
                "woo_conversions": woo["conversions"],
                "shopify_conversions": shopify["conversions"],
            }
        )

    monthly_values: dict[int, dict[str, float]] = defaultdict(
        lambda: {
            "woo_cost": 0.0,
            "woo_conversion_value": 0.0,
            "shopify_cost": 0.0,
            "shopify_conversion_value": 0.0,
        }
    )
    for row in comparison_weeks:
        month = int(str(row["shopify_week_start"])[5:7])
        for field in monthly_values[month]:
            monthly_values[month][field] += float(row[field])
    monthly_comparison = []
    for month, values in sorted(monthly_values.items()):
        woo_roas = values["woo_conversion_value"] / values["woo_cost"]
        shopify_roas = (
            values["shopify_conversion_value"] / values["shopify_cost"]
        )
        monthly_comparison.append(
            {
                "month_number": month,
                "month": calendar.month_abbr[month],
                **values,
                "woo_roas": woo_roas,
                "shopify_roas": shopify_roas,
                "shopify_vs_woo_roas_change": shopify_roas / woo_roas - 1,
            }
        )

    maturity_sensitivity = []
    for weeks, label in (
        (28, "All 28 weeks through July 19"),
        (26, "Exclude latest 2 weeks"),
        (24, "Exclude latest 4 weeks"),
    ):
        rows = comparison_weeks[:weeks]
        woo_roas = sum(float(row["woo_conversion_value"]) for row in rows) / sum(
            float(row["woo_cost"]) for row in rows
        )
        shopify_roas = sum(
            float(row["shopify_conversion_value"]) for row in rows
        ) / sum(float(row["shopify_cost"]) for row in rows)
        maturity_sensitivity.append(
            {
                "window": label,
                "weeks": weeks,
                "woo_roas": woo_roas,
                "shopify_roas": shopify_roas,
                "shopify_vs_woo_roas_change": shopify_roas / woo_roas - 1,
            }
        )

    random_generator = random.Random(BOOTSTRAP_SEED)
    relative_differences: list[float] = []
    absolute_differences: list[float] = []
    for _ in range(BOOTSTRAP_SAMPLES):
        indices = [random_generator.randrange(len(woo_rows)) for _ in woo_rows]
        woo_sample = [woo_rows[index] for index in indices]
        shopify_sample = [shopify_rows[index] for index in indices]
        woo_roas = float(aggregate(woo_sample)["roas"])
        shopify_roas = float(aggregate(shopify_sample)["roas"])
        relative_differences.append(shopify_roas / woo_roas - 1)
        absolute_differences.append(shopify_roas - woo_roas)
    relative_differences.sort()
    absolute_differences.sort()

    pricing_event_sensitivity = {
        "record": {
            "workflow_run_at_utc": "2026-04-09T16:18:45Z",
            "pricing_policy_documented_on": "2026-04-11",
            "issue": (
                "Variant price and compare-at-price sale mutation could restore "
                "from an already-corrupted baseline."
            ),
        },
        "exclude_incident_weeks": paired_exclusion_summary(
            comparison_weeks, PRICING_INCIDENT_WEEKS
        ),
        "exclude_incident_plus_following_attribution_week": paired_exclusion_summary(
            comparison_weeks, PRICING_CONSERVATIVE_WEEKS
        ),
    }

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "campaign": {"id": 20647427212, "name": "Performance Max-2"},
        "metric_definition": "ROAS = purchase conversion value / Google Ads cost",
        "periods": {
            "WooCommerce": {
                "start": WOO_START,
                "end": WOO_END,
                "purchase_action": WOO_ACTION,
            },
            "Shopify": {
                "start": SHOPIFY_START,
                "end": SHOPIFY_END,
                "purchase_action": SHOPIFY_ACTION,
            },
        },
        "excluded": {
            "shopify_setup_period": "2025-10-01 through 2025-12-31",
            "transition_weeks": ["2025-10-13", "2025-10-20"],
            "duplicate_purchase_action": "[85ed] Google for WooCommerce purchase action",
        },
        "platform_summary": {
            "WooCommerce": woo_summary,
            "Shopify": shopify_summary,
        },
        "shopify_vs_woo_percent_change": comparisons,
        "paired_week_bootstrap": {
            "samples": BOOTSTRAP_SAMPLES,
            "seed": BOOTSTRAP_SEED,
            "relative_roas_difference_95_interval": [
                quantile(relative_differences, 0.025),
                quantile(relative_differences, 0.975),
            ],
            "absolute_roas_difference_95_interval": [
                quantile(absolute_differences, 0.025),
                quantile(absolute_differences, 0.975),
            ],
            "shopify_weekly_roas_win_rate": sum(
                float(shopify["roas"]) > float(woo["roas"])
                for woo, shopify in zip(woo_rows, shopify_rows)
            )
            / len(woo_rows),
        },
        "comparison_weeks": comparison_weeks,
        "monthly_comparison": monthly_comparison,
        "maturity_sensitivity": maturity_sensitivity,
        "known_event_analysis": {
            "pricing_incident": pricing_event_sensitivity,
            "scalamandre_catalog_expansion": scalamandre_event_summary(input_dir),
        },
        "notes": [
            "Periods contain 28 complete January-through-July weeks separated by 364 days.",
            "WooCommerce uses SR Sales only; the duplicate WooCommerce purchase action is excluded.",
            "Shopify uses Google Shopping App Purchase only.",
            "The two tracking transition weeks beginning 2025-10-13 and 2025-10-20 are excluded.",
            "October through December 2025 is excluded because the Shopify store was not fully set up.",
            "This is an observational era comparison; spend, demand, bidding, and other conditions differ.",
            "Google Ads standard conversion metrics are attributed to interaction date; event-window exclusions therefore include a conservative following week sensitivity.",
            "The Scalamandre feed expansion is evaluated separately using product IDs from the Shopify import range.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        help="Dated campaign-performance directory; defaults to the latest export.",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    input_dir = args.input_dir or latest_input_dir(
        Path("google/data/campaign-performance")
    )
    output_path = args.output or input_dir / "max-2-woo-vs-shopify-analysis.json"
    analysis = run_analysis(input_dir)
    output_path.write_text(
        json.dumps(analysis, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote WooCommerce versus Shopify analysis to {output_path}")


if __name__ == "__main__":
    main()

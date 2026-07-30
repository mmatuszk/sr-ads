#!/usr/bin/env python3
"""Export weekly Shopping-product performance for one Google Ads campaign."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path

from export_campaign_weekly_performance import (
    DEFAULT_CAMPAIGN_ID,
    build_client,
    get_campaign_metadata,
)
from verify_google_ads_access import DEFAULT_CONFIG, load_config


DEFAULT_START_DATE = date(2026, 1, 5)
DEFAULT_END_DATE = date(2026, 7, 19)


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid ISO date: {value}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--campaign-id", type=int, default=DEFAULT_CAMPAIGN_ID)
    parser.add_argument("--start-date", type=parse_date, default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", type=parse_date, default=DEFAULT_END_DATE)
    parser.add_argument("--direct", action="store_true")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("google/data/campaign-performance/2026-07-21"),
    )
    args = parser.parse_args()
    if args.end_date < args.start_date:
        parser.error("--end-date must be on or after --start-date")

    config = load_config(args.config)
    customer_id = config["customer_id"]
    client = build_client(config, direct=args.direct)
    service = client.get_service("GoogleAdsService")
    campaign = get_campaign_metadata(service, customer_id, args.campaign_id)

    query = f"""
        SELECT
          campaign.id,
          segments.week,
          segments.product_item_id,
          segments.product_title,
          segments.product_brand,
          segments.product_type_l1,
          segments.product_custom_attribute0,
          segments.product_custom_attribute1,
          segments.product_custom_attribute2,
          segments.product_custom_attribute3,
          segments.product_custom_attribute4,
          segments.product_merchant_id,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions,
          metrics.conversions_value
        FROM shopping_performance_view
        WHERE campaign.id = {campaign.campaign_id}
          AND segments.date BETWEEN '{args.start_date}' AND '{args.end_date}'
        ORDER BY segments.week, segments.product_brand, segments.product_item_id
    """
    rows: list[dict[str, object]] = []
    for row in service.search(customer_id=customer_id, query=query):
        rows.append(
            {
                "week_start": row.segments.week,
                "product_item_id": row.segments.product_item_id,
                "product_title": row.segments.product_title,
                "product_brand": row.segments.product_brand,
                "product_type_l1": row.segments.product_type_l1,
                "product_custom_attribute0": row.segments.product_custom_attribute0,
                "product_custom_attribute1": row.segments.product_custom_attribute1,
                "product_custom_attribute2": row.segments.product_custom_attribute2,
                "product_custom_attribute3": row.segments.product_custom_attribute3,
                "product_custom_attribute4": row.segments.product_custom_attribute4,
                "product_merchant_id": row.segments.product_merchant_id,
                "impressions": int(row.metrics.impressions),
                "clicks": int(row.metrics.clicks),
                "cost": f"{float(row.metrics.cost_micros) / 1_000_000:.6f}",
                "conversions": f"{float(row.metrics.conversions):.6f}",
                "conversion_value": f"{float(row.metrics.conversions_value):.6f}",
            }
        )

    if not rows:
        raise SystemExit("No product-performance rows returned")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "performance-max-2-weekly-products.csv"
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    metadata_path = args.output_dir / "performance-max-2-weekly-products-metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "customer_id": customer_id,
                "campaign_id": campaign.campaign_id,
                "campaign_name": campaign.campaign_name,
                "start_date": args.start_date.isoformat(),
                "end_date": args.end_date.isoformat(),
                "row_count": len(rows),
                "source": "Google Ads API shopping_performance_view",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(rows):,} rows to {output_path}")


if __name__ == "__main__":
    main()

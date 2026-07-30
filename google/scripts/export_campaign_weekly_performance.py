#!/usr/bin/env python3
"""Export complete-week Google Ads campaign performance to CSV files."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from verify_google_ads_access import DEFAULT_CONFIG, load_config


DEFAULT_CAMPAIGN_ID = 20647427212
DEFAULT_WEEKS = 104


@dataclass(frozen=True)
class AccountMetadata:
    account_id: int
    account_name: str
    currency_code: str
    time_zone: str


@dataclass(frozen=True)
class CampaignMetadata:
    campaign_id: int
    campaign_name: str
    status: str
    channel_type: str


def build_client(config: dict[str, str], *, direct: bool) -> GoogleAdsClient:
    client_config: dict[str, str | bool] = {
        "developer_token": config["developer_token"],
        "use_application_default_credentials": True,
        "use_proto_plus": True,
    }
    if not direct:
        client_config["login_customer_id"] = config["login_customer_id"]
    return GoogleAdsClient.load_from_dict(client_config)


def get_account_metadata(service: object, customer_id: str) -> AccountMetadata:
    rows = service.search(
        customer_id=customer_id,
        query="""
            SELECT
              customer.id,
              customer.descriptive_name,
              customer.currency_code,
              customer.time_zone
            FROM customer
            LIMIT 1
        """,
    )
    customer = next(iter(rows)).customer
    return AccountMetadata(
        account_id=customer.id,
        account_name=customer.descriptive_name,
        currency_code=customer.currency_code,
        time_zone=customer.time_zone,
    )


def get_campaign_metadata(
    service: object, customer_id: str, campaign_id: int
) -> CampaignMetadata:
    rows = list(
        service.search(
            customer_id=customer_id,
            query=f"""
                SELECT
                  campaign.id,
                  campaign.name,
                  campaign.status,
                  campaign.advertising_channel_type
                FROM campaign
                WHERE campaign.id = {campaign_id}
                LIMIT 1
            """,
        )
    )
    if not rows:
        raise SystemExit(f"Campaign not found: {campaign_id}")
    campaign = rows[0].campaign
    return CampaignMetadata(
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        status=campaign.status.name,
        channel_type=campaign.advertising_channel_type.name,
    )


def complete_week_window(time_zone: str, weeks: int) -> tuple[date, date]:
    if weeks < 1:
        raise SystemExit("--weeks must be at least 1")
    today = datetime.now(ZoneInfo(time_zone)).date()
    last_sunday = today - timedelta(days=today.weekday() + 1)
    first_monday = last_sunday - timedelta(days=(weeks * 7) - 1)
    return first_monday, last_sunday


def safe_ratio(numerator: float, denominator: float) -> str:
    if denominator == 0:
        return ""
    return f"{numerator / denominator:.6f}"


def weekly_rows(
    service: object,
    customer_id: str,
    campaign: CampaignMetadata,
    start_date: date,
    end_date: date,
) -> list[dict[str, object]]:
    query = f"""
        SELECT
          segments.week,
          metrics.impressions,
          metrics.clicks,
          metrics.interactions,
          metrics.cost_micros,
          metrics.conversions,
          metrics.conversions_value,
          metrics.all_conversions,
          metrics.all_conversions_value
        FROM campaign
        WHERE campaign.id = {campaign.campaign_id}
          AND segments.date BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
        ORDER BY segments.week
    """
    by_week: dict[str, object] = {}
    for row in service.search(customer_id=customer_id, query=query):
        by_week[row.segments.week] = row.metrics

    output: list[dict[str, object]] = []
    week_start = start_date
    while week_start <= end_date:
        week_key = week_start.isoformat()
        metrics = by_week.get(week_key)
        impressions = int(metrics.impressions) if metrics else 0
        clicks = int(metrics.clicks) if metrics else 0
        interactions = int(metrics.interactions) if metrics else 0
        cost = float(metrics.cost_micros) / 1_000_000 if metrics else 0.0
        conversions = float(metrics.conversions) if metrics else 0.0
        conversion_value = float(metrics.conversions_value) if metrics else 0.0
        all_conversions = float(metrics.all_conversions) if metrics else 0.0
        all_conversion_value = float(metrics.all_conversions_value) if metrics else 0.0
        output.append(
            {
                "week_start": week_key,
                "week_end": (week_start + timedelta(days=6)).isoformat(),
                "campaign_id": campaign.campaign_id,
                "campaign_name": campaign.campaign_name,
                "api_row_returned": metrics is not None,
                "impressions": impressions,
                "clicks": clicks,
                "interactions": interactions,
                "cost": f"{cost:.6f}",
                "conversions": f"{conversions:.6f}",
                "conversion_value": f"{conversion_value:.6f}",
                "roas": safe_ratio(conversion_value, cost),
                "ctr": safe_ratio(clicks, impressions),
                "average_cpc": safe_ratio(cost, clicks),
                "conversion_rate": safe_ratio(conversions, interactions),
                "average_conversion_value": safe_ratio(conversion_value, conversions),
                "all_conversions": f"{all_conversions:.6f}",
                "all_conversion_value": f"{all_conversion_value:.6f}",
            }
        )
        week_start += timedelta(days=7)
    return output


def conversion_action_rows(
    service: object,
    customer_id: str,
    campaign: CampaignMetadata,
    start_date: date,
    end_date: date,
) -> list[dict[str, object]]:
    query = f"""
        SELECT
          segments.week,
          segments.conversion_action,
          segments.conversion_action_name,
          segments.conversion_action_category,
          metrics.conversions,
          metrics.conversions_value,
          metrics.all_conversions,
          metrics.all_conversions_value
        FROM campaign
        WHERE campaign.id = {campaign.campaign_id}
          AND segments.date BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
        ORDER BY segments.week, segments.conversion_action_name
    """
    output: list[dict[str, object]] = []
    for row in service.search(customer_id=customer_id, query=query):
        output.append(
            {
                "week_start": row.segments.week,
                "week_end": (
                    date.fromisoformat(row.segments.week) + timedelta(days=6)
                ).isoformat(),
                "campaign_id": campaign.campaign_id,
                "campaign_name": campaign.campaign_name,
                "conversion_action_resource": row.segments.conversion_action,
                "conversion_action_name": row.segments.conversion_action_name,
                "conversion_action_category": row.segments.conversion_action_category.name,
                "conversions": f"{float(row.metrics.conversions):.6f}",
                "conversion_value": f"{float(row.metrics.conversions_value):.6f}",
                "all_conversions": f"{float(row.metrics.all_conversions):.6f}",
                "all_conversion_value": f"{float(row.metrics.all_conversions_value):.6f}",
            }
        )
    return output


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise SystemExit(f"No rows returned for {path.name}")
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def file_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "campaign"


def value_action_overlap_weeks(rows: list[dict[str, object]]) -> list[str]:
    value_actions_by_week: dict[str, set[str]] = {}
    for row in rows:
        if float(row["conversion_value"]) <= 0:
            continue
        value_actions_by_week.setdefault(str(row["week_start"]), set()).add(
            str(row["conversion_action_resource"])
        )
    return sorted(
        week for week, actions in value_actions_by_week.items() if len(actions) > 1
    )


def adjusted_weekly_rows(
    campaign_rows: list[dict[str, object]],
    action_rows: list[dict[str, object]],
    excluded_action_names: list[str],
) -> list[dict[str, object]]:
    excluded_by_week: dict[str, tuple[float, float]] = {}
    excluded_names = set(excluded_action_names)
    for row in action_rows:
        if row["conversion_action_name"] not in excluded_names:
            continue
        week = str(row["week_start"])
        conversions, value = excluded_by_week.get(week, (0.0, 0.0))
        excluded_by_week[week] = (
            conversions + float(row["conversions"]),
            value + float(row["conversion_value"]),
        )

    output: list[dict[str, object]] = []
    for row in campaign_rows:
        week = str(row["week_start"])
        excluded_conversions, excluded_value = excluded_by_week.get(
            week, (0.0, 0.0)
        )
        reported_conversions = float(row["conversions"])
        reported_value = float(row["conversion_value"])
        cost = float(row["cost"])
        adjusted_conversions = max(0.0, reported_conversions - excluded_conversions)
        adjusted_value = max(0.0, reported_value - excluded_value)
        output.append(
            {
                "week_start": week,
                "week_end": row["week_end"],
                "campaign_id": row["campaign_id"],
                "campaign_name": row["campaign_name"],
                "impressions": row["impressions"],
                "clicks": row["clicks"],
                "interactions": row["interactions"],
                "cost": row["cost"],
                "reported_conversions": row["conversions"],
                "reported_conversion_value": row["conversion_value"],
                "reported_roas": row["roas"],
                "excluded_conversions": f"{excluded_conversions:.6f}",
                "excluded_conversion_value": f"{excluded_value:.6f}",
                "adjusted_conversions": f"{adjusted_conversions:.6f}",
                "adjusted_conversion_value": f"{adjusted_value:.6f}",
                "adjusted_roas": safe_ratio(adjusted_value, cost),
                "ctr": row["ctr"],
                "average_cpc": row["average_cpc"],
                "adjusted_conversion_rate": safe_ratio(
                    adjusted_conversions, float(row["interactions"])
                ),
                "adjusted_average_conversion_value": safe_ratio(
                    adjusted_value, adjusted_conversions
                ),
            }
        )
    return output


def export(args: argparse.Namespace) -> None:
    config = load_config(args.config.expanduser())
    client = build_client(config, direct=args.direct)
    service = client.get_service("GoogleAdsService")
    account = get_account_metadata(service, config["customer_id"])
    campaign = get_campaign_metadata(
        service, config["customer_id"], args.campaign_id
    )
    start_date, end_date = complete_week_window(account.time_zone, args.weeks)
    output_dir = args.output_dir or Path(
        "google/data/campaign-performance",
        datetime.now(ZoneInfo(account.time_zone)).date().isoformat(),
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    campaign_rows = weekly_rows(
        service, config["customer_id"], campaign, start_date, end_date
    )
    action_rows = conversion_action_rows(
        service, config["customer_id"], campaign, start_date, end_date
    )
    prefix = file_slug(campaign.campaign_name)
    campaign_path = output_dir / f"{prefix}-weekly-campaign.csv"
    actions_path = output_dir / f"{prefix}-weekly-conversion-actions.csv"
    metadata_path = output_dir / "metadata.json"
    write_csv(campaign_path, campaign_rows)
    write_csv(actions_path, action_rows)
    overlap_weeks = value_action_overlap_weeks(action_rows)
    adjusted_path = output_dir / f"{prefix}-weekly-adjusted.csv"
    adjusted_rows: list[dict[str, object]] = []
    if args.exclude_conversion_action_name:
        adjusted_rows = adjusted_weekly_rows(
            campaign_rows,
            action_rows,
            args.exclude_conversion_action_name,
        )
        write_csv(adjusted_path, adjusted_rows)

    metadata = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Google Ads API",
        "read_only": True,
        "account": asdict(account),
        "campaign": asdict(campaign),
        "reporting_window": {
            "week_definition": "Monday through Sunday",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "complete_weeks": args.weeks,
            "current_partial_week_excluded": True,
        },
        "files": {
            campaign_path.name: {"rows": len(campaign_rows)},
            actions_path.name: {"rows": len(action_rows)},
        },
        "adjustment": {
            "excluded_conversion_action_names": args.exclude_conversion_action_name,
            "method": "Subtract excluded actions from reported conversions and conversion value; retain reported cost.",
        },
        "data_quality": {
            "weeks_with_multiple_value_bearing_conversion_actions": overlap_weeks,
            "weeks_with_multiple_value_bearing_conversion_actions_count": len(
                overlap_weeks
            ),
        },
        "notes": [
            "Currency metrics are converted from micros to account currency.",
            "Derived rates are stored as decimal ratios, not percentages.",
            "Conversion data can be restated after retrieval because of attribution lag.",
            "Weeks without a Google Ads metrics row are emitted with zeros and api_row_returned=false.",
            "Multiple value-bearing conversion actions in one week can indicate tracking overlap; review conversion-action detail before interpreting ROAS.",
        ],
    }
    if adjusted_rows:
        metadata["files"][adjusted_path.name] = {"rows": len(adjusted_rows)}
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(f"Exported {len(campaign_rows)} complete campaign weeks to {campaign_path}")
    print(f"Exported {len(action_rows)} conversion-action rows to {actions_path}")
    if adjusted_rows:
        print(f"Exported {len(adjusted_rows)} adjusted weeks to {adjusted_path}")
    print(f"Wrote retrieval metadata to {metadata_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--campaign-id", type=int, default=DEFAULT_CAMPAIGN_ID)
    parser.add_argument("--weeks", type=int, default=DEFAULT_WEEKS)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--exclude-conversion-action-name",
        action="append",
        default=[],
        help="Create an adjusted weekly file that subtracts this conversion action; repeatable.",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Omit login_customer_id and use the OAuth user's direct account access.",
    )
    args = parser.parse_args()

    try:
        export(args)
    except GoogleAdsException as exc:
        print(f"Google Ads API request failed: {exc.error.code().name}")
        for error in exc.failure.errors:
            print(f"- {error.message}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

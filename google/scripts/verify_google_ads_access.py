#!/usr/bin/env python3
"""Verify read-only Google Ads API access using ADC credentials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


DEFAULT_CONFIG = Path("~/.config/sr-ads/google_ads.json").expanduser()


def load_config(path: Path) -> dict[str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Google Ads config not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Google Ads config is not valid JSON: {path}") from exc

    required = ("developer_token", "login_customer_id", "customer_id")
    missing = [key for key in required if not str(data.get(key, "")).strip()]
    if missing:
        raise SystemExit(f"Google Ads config is missing: {', '.join(missing)}")

    return {
        "developer_token": str(data["developer_token"]).strip(),
        "login_customer_id": str(data["login_customer_id"]).replace("-", "").strip(),
        "customer_id": str(data["customer_id"]).replace("-", "").strip(),
    }


def verify_access(config: dict[str, str], *, direct: bool = False) -> None:
    client_config: dict[str, str | bool] = {
        "developer_token": config["developer_token"],
        "use_application_default_credentials": True,
        "use_proto_plus": True,
    }
    if not direct:
        client_config["login_customer_id"] = config["login_customer_id"]

    client = GoogleAdsClient.load_from_dict(client_config)
    service = client.get_service("GoogleAdsService")

    customer_rows = service.search(
        customer_id=config["customer_id"],
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
    customer = next(iter(customer_rows)).customer

    campaign_rows = service.search(
        customer_id=config["customer_id"],
        query="""
            SELECT
              campaign.id,
              campaign.name,
              campaign.status
            FROM campaign
            ORDER BY campaign.id
        """,
    )
    campaigns = list(campaign_rows)

    print("Google Ads API access verified (read-only).")
    print(f"Account: {customer.descriptive_name} ({customer.id})")
    print(f"Currency: {customer.currency_code}")
    print(f"Time zone: {customer.time_zone}")
    print(f"Campaigns returned: {len(campaigns)}")
    for row in campaigns[:20]:
        print(f"- {row.campaign.id}: {row.campaign.name} [{row.campaign.status.name}]")
    if len(campaigns) > 20:
        print(f"- ... {len(campaigns) - 20} additional campaigns")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Omit login_customer_id and use the OAuth user's direct account access.",
    )
    args = parser.parse_args()

    try:
        verify_access(
            load_config(args.config.expanduser()),
            direct=args.direct,
        )
    except GoogleAdsException as exc:
        print(f"Google Ads API request failed: {exc.error.code().name}")
        for error in exc.failure.errors:
            print(f"- {error.message}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

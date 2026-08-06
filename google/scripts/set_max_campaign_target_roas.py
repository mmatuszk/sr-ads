#!/usr/bin/env python3
"""Plan or set target ROAS for the guarded Max-2 and Max-13 campaigns."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google.api_core import protobuf_helpers


DEFAULT_CONFIG = Path("~/.config/sr-ads/google_ads.json").expanduser()
EXPECTED_CAMPAIGNS = {
    20647427212: "Performance Max-2",
    23453016844: "Performance Max-13",
}


@dataclass(frozen=True)
class CampaignState:
    campaign_id: int
    name: str
    status: str
    channel: str
    strategy: str
    target_roas: float


def load_config(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = ("developer_token", "login_customer_id", "customer_id")
    missing = [key for key in required if not str(data.get(key, "")).strip()]
    if missing:
        raise SystemExit(f"Google Ads config is missing: {', '.join(missing)}")
    return {
        "developer_token": str(data["developer_token"]).strip(),
        "login_customer_id": str(data["login_customer_id"]).replace("-", "").strip(),
        "customer_id": str(data["customer_id"]).replace("-", "").strip(),
    }


def make_client(config: dict[str, str]) -> GoogleAdsClient:
    return GoogleAdsClient.load_from_dict(
        {
            "developer_token": config["developer_token"],
            "login_customer_id": config["login_customer_id"],
            "use_application_default_credentials": True,
            "use_proto_plus": True,
        }
    )


def query_campaigns(client: GoogleAdsClient, customer_id: str) -> list[CampaignState]:
    ids = ", ".join(str(campaign_id) for campaign_id in EXPECTED_CAMPAIGNS)
    rows = client.get_service("GoogleAdsService").search(
        customer_id=customer_id,
        query=f"""
            SELECT campaign.id, campaign.name, campaign.status,
              campaign.advertising_channel_type,
              campaign.bidding_strategy_type,
              campaign.maximize_conversion_value.target_roas
            FROM campaign
            WHERE campaign.id IN ({ids})
            ORDER BY campaign.id
        """,
    )
    states = [
        CampaignState(
            campaign_id=row.campaign.id,
            name=row.campaign.name,
            status=row.campaign.status.name,
            channel=row.campaign.advertising_channel_type.name,
            strategy=row.campaign.bidding_strategy_type.name,
            target_roas=row.campaign.maximize_conversion_value.target_roas,
        )
        for row in rows
    ]
    validate_campaigns(states)
    return states


def validate_campaigns(states: list[CampaignState]) -> None:
    found = {state.campaign_id: state for state in states}
    if set(found) != set(EXPECTED_CAMPAIGNS):
        raise SystemExit(
            f"Guarded campaign set changed: expected {sorted(EXPECTED_CAMPAIGNS)}, "
            f"found {sorted(found)}"
        )
    for campaign_id, expected_name in EXPECTED_CAMPAIGNS.items():
        state = found[campaign_id]
        if state.name != expected_name:
            raise SystemExit(
                f"Campaign {campaign_id} is named {state.name!r}, not {expected_name!r}"
            )
        if state.status != "ENABLED":
            raise SystemExit(f"Campaign {campaign_id} is {state.status}, not ENABLED")
        if state.channel != "PERFORMANCE_MAX":
            raise SystemExit(
                f"Campaign {campaign_id} is {state.channel}, not PERFORMANCE_MAX"
            )
        if state.strategy != "MAXIMIZE_CONVERSION_VALUE":
            raise SystemExit(
                f"Campaign {campaign_id} uses {state.strategy}, not "
                "MAXIMIZE_CONVERSION_VALUE"
            )


def build_operations(
    client: GoogleAdsClient,
    customer_id: str,
    states: list[CampaignState],
    target_roas: float,
):
    campaign_service = client.get_service("CampaignService")
    operations = []
    for state in states:
        if math.isclose(state.target_roas, target_roas, rel_tol=0, abs_tol=1e-9):
            continue
        operation = client.get_type("CampaignOperation")
        campaign = operation.update
        campaign.resource_name = campaign_service.campaign_path(
            customer_id, str(state.campaign_id)
        )
        campaign.maximize_conversion_value.target_roas = target_roas
        operation.update_mask.CopyFrom(
            protobuf_helpers.field_mask(None, campaign._pb)
        )
        operations.append(operation)
    return operations


def print_plan(states: list[CampaignState], target_roas: float) -> None:
    print("Target ROAS campaign plan")
    print(f"Desired target: {target_roas * 100:.2f}%")
    for state in states:
        action = (
            "unchanged"
            if math.isclose(state.target_roas, target_roas, rel_tol=0, abs_tol=1e-9)
            else "update"
        )
        print(
            f"- {state.campaign_id} {state.name}: "
            f"{state.target_roas * 100:.8f}% -> {target_roas * 100:.2f}% "
            f"[{action}]"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--target-roas-percent", type=float, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-customer-id")
    parser.add_argument(
        "--confirm-campaign-id",
        action="append",
        type=int,
        default=[],
        help="Repeat once for each guarded campaign ID.",
    )
    parser.add_argument("--confirm-target-roas-percent", type=float)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not math.isfinite(args.target_roas_percent) or args.target_roas_percent <= 0:
        raise SystemExit("--target-roas-percent must be a positive finite number")
    target_roas = args.target_roas_percent / 100
    config = load_config(args.config.expanduser())
    client = make_client(config)

    try:
        states = query_campaigns(client, config["customer_id"])
        print_plan(states, target_roas)
        operations = build_operations(client, config["customer_id"], states, target_roas)
        if not args.apply:
            print(f"Dry run: {len(operations)} campaign update(s); no changes made.")
            return

        if args.confirm_customer_id != config["customer_id"]:
            raise SystemExit("--confirm-customer-id does not match the operating account")
        if set(args.confirm_campaign_id) != set(EXPECTED_CAMPAIGNS):
            raise SystemExit(
                "--confirm-campaign-id values must exactly match both guarded campaigns"
            )
        if args.confirm_target_roas_percent is None or not math.isclose(
            args.confirm_target_roas_percent,
            args.target_roas_percent,
            rel_tol=0,
            abs_tol=1e-9,
        ):
            raise SystemExit(
                "--confirm-target-roas-percent must exactly match --target-roas-percent"
            )
        if operations:
            response = client.get_service("CampaignService").mutate_campaigns(
                customer_id=config["customer_id"], operations=operations
            )
            print(f"Applied {len(response.results)} campaign update(s).")
        else:
            print("No campaign updates were required.")

        verified = query_campaigns(client, config["customer_id"])
        for state in verified:
            if not math.isclose(state.target_roas, target_roas, rel_tol=0, abs_tol=1e-9):
                raise SystemExit(
                    f"Verification failed for campaign {state.campaign_id}: "
                    f"found {state.target_roas}, expected {target_roas}"
                )
        print("Verified both campaigns at the requested target ROAS.")
        print_plan(verified, target_roas)
    except GoogleAdsException as exc:
        print(f"Google Ads API request failed: {exc.error.code().name}")
        for error in exc.failure.errors:
            print(f"- {error.message}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

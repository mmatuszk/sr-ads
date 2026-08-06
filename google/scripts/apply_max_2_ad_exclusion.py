#!/usr/bin/env python3
"""Exclude GMC custom_label_1=exclude from both Max-2 asset groups.

The command is read-only by default. Live changes require --apply plus exact
customer and campaign confirmations. Existing subdivisions are preserved; each
currently included leaf is replaced with a custom_label_1 gate that excludes
the value ``exclude`` and includes all other values.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


DEFAULT_CONFIG = Path("~/.config/sr-ads/google_ads.json").expanduser()
CAMPAIGN_ID = 20647427212
CAMPAIGN_NAME = "Performance Max-2"
EXPECTED_ASSET_GROUPS = {
    6479076289: "Performance Max-2",
    6734634322: "Performance Max-2 Control",
}
LABEL_VALUE = "exclude"


@dataclass
class ListingNode:
    resource_name: str
    asset_group_id: int
    node_type: str
    parent: str
    case_value: object


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


def query_state(client: GoogleAdsClient, customer_id: str) -> tuple[dict[int, str], list[ListingNode]]:
    service = client.get_service("GoogleAdsService")
    campaign_rows = list(
        service.search(
            customer_id=customer_id,
            query=f"""
                SELECT campaign.id, campaign.name, asset_group.id,
                  asset_group.name, asset_group.status
                FROM asset_group
                WHERE campaign.id = {CAMPAIGN_ID}
                  AND asset_group.status = ENABLED
                ORDER BY asset_group.id
            """,
        )
    )
    if not campaign_rows:
        raise SystemExit(f"Campaign {CAMPAIGN_ID} was not found or has no enabled asset groups")
    if any(row.campaign.name != CAMPAIGN_NAME for row in campaign_rows):
        raise SystemExit(f"Campaign {CAMPAIGN_ID} is not named {CAMPAIGN_NAME!r}")
    asset_groups = {row.asset_group.id: row.asset_group.name for row in campaign_rows}
    if asset_groups != EXPECTED_ASSET_GROUPS:
        raise SystemExit(
            "Enabled asset groups do not match the guarded set: "
            f"expected {EXPECTED_ASSET_GROUPS}, found {asset_groups}"
        )

    rows = service.search(
        customer_id=customer_id,
        query=f"""
            SELECT asset_group.id,
              asset_group_listing_group_filter.resource_name,
              asset_group_listing_group_filter.type,
              asset_group_listing_group_filter.listing_source,
              asset_group_listing_group_filter.parent_listing_group_filter,
              asset_group_listing_group_filter.case_value.product_brand.value,
              asset_group_listing_group_filter.case_value.product_category.category_id,
              asset_group_listing_group_filter.case_value.product_category.level,
              asset_group_listing_group_filter.case_value.product_channel.channel,
              asset_group_listing_group_filter.case_value.product_condition.condition,
              asset_group_listing_group_filter.case_value.product_custom_attribute.index,
              asset_group_listing_group_filter.case_value.product_custom_attribute.value,
              asset_group_listing_group_filter.case_value.product_item_id.value,
              asset_group_listing_group_filter.case_value.product_type.level,
              asset_group_listing_group_filter.case_value.product_type.value,
              asset_group_listing_group_filter.case_value.retail_filter_bundle.shared_set,
              asset_group_listing_group_filter.case_value.webpage.conditions
            FROM asset_group_listing_group_filter
            WHERE campaign.id = {CAMPAIGN_ID}
              AND asset_group.status = ENABLED
            ORDER BY asset_group.id, asset_group_listing_group_filter.id
        """,
    )
    nodes: list[ListingNode] = []
    for row in rows:
        node = row.asset_group_listing_group_filter
        if node.listing_source.name != "SHOPPING":
            raise SystemExit(f"Unexpected non-Shopping listing source: {node.resource_name}")
        nodes.append(
            ListingNode(
                resource_name=node.resource_name,
                asset_group_id=row.asset_group.id,
                node_type=node.type_.name,
                parent=node.parent_listing_group_filter,
                case_value=node.case_value,
            )
        )
    return asset_groups, nodes


def case_kind(case_value: object) -> str | None:
    return case_value._pb.WhichOneof("dimension")


def is_label_exclusion_gate(node: ListingNode, children: dict[str, list[ListingNode]]) -> bool:
    if node.node_type != "SUBDIVISION":
        return False
    node_children = children[node.resource_name]
    excluded = [
        child
        for child in node_children
        if child.node_type == "UNIT_EXCLUDED"
        and case_kind(child.case_value) == "product_custom_attribute"
        and child.case_value.product_custom_attribute.index.name == "INDEX1"
        and child.case_value.product_custom_attribute.value == LABEL_VALUE
    ]
    included_other = [
        child
        for child in node_children
        if child.node_type == "UNIT_INCLUDED"
        and case_kind(child.case_value) == "product_custom_attribute"
        and child.case_value.product_custom_attribute.index.name == "INDEX1"
        and not child.case_value.product_custom_attribute.value
    ]
    return len(excluded) == 1 and len(included_other) == 1 and len(node_children) == 2


def included_leaves_to_wrap(nodes: list[ListingNode]) -> list[ListingNode]:
    by_name = {node.resource_name: node for node in nodes}
    children: dict[str, list[ListingNode]] = defaultdict(list)
    for node in nodes:
        children[node.parent].append(node)

    protected_included_leaves = {
        child.resource_name
        for node in nodes
        if is_label_exclusion_gate(node, children)
        for child in children[node.resource_name]
        if child.node_type == "UNIT_INCLUDED"
    }
    leaves = [
        node
        for node in nodes
        if node.node_type == "UNIT_INCLUDED"
        and not children[node.resource_name]
        and node.resource_name not in protected_included_leaves
    ]
    for leaf in leaves:
        if leaf.parent and leaf.parent not in by_name:
            raise SystemExit(f"Listing group parent is missing: {leaf.parent}")
    return leaves


def build_operations(client: GoogleAdsClient, customer_id: str, leaves: list[ListingNode]):
    service = client.get_service("AssetGroupListingGroupFilterService")
    operations = []
    next_temp_id = -1

    for leaf in leaves:
        remove = client.get_type("AssetGroupListingGroupFilterOperation")
        remove.remove = leaf.resource_name
        operations.append(remove)

        subdivision_name = service.asset_group_listing_group_filter_path(
            customer_id, str(leaf.asset_group_id), str(next_temp_id)
        )
        next_temp_id -= 1
        create_subdivision = client.get_type("AssetGroupListingGroupFilterOperation")
        subdivision = create_subdivision.create
        subdivision.resource_name = subdivision_name
        subdivision.asset_group = client.get_service("AssetGroupService").asset_group_path(
            customer_id, str(leaf.asset_group_id)
        )
        subdivision.type_ = client.enums.ListingGroupFilterTypeEnum.SUBDIVISION
        subdivision.listing_source = client.enums.ListingGroupFilterListingSourceEnum.SHOPPING
        subdivision.parent_listing_group_filter = leaf.parent
        if case_kind(leaf.case_value) is not None:
            subdivision.case_value = leaf.case_value
        operations.append(create_subdivision)

        excluded_name = service.asset_group_listing_group_filter_path(
            customer_id, str(leaf.asset_group_id), str(next_temp_id)
        )
        next_temp_id -= 1
        create_excluded = client.get_type("AssetGroupListingGroupFilterOperation")
        excluded = create_excluded.create
        excluded.resource_name = excluded_name
        excluded.asset_group = subdivision.asset_group
        excluded.type_ = client.enums.ListingGroupFilterTypeEnum.UNIT_EXCLUDED
        excluded.listing_source = client.enums.ListingGroupFilterListingSourceEnum.SHOPPING
        excluded.parent_listing_group_filter = subdivision_name
        excluded.case_value.product_custom_attribute.index = (
            client.enums.ListingGroupFilterCustomAttributeIndexEnum.INDEX1
        )
        excluded.case_value.product_custom_attribute.value = LABEL_VALUE
        operations.append(create_excluded)

        included_name = service.asset_group_listing_group_filter_path(
            customer_id, str(leaf.asset_group_id), str(next_temp_id)
        )
        next_temp_id -= 1
        create_included = client.get_type("AssetGroupListingGroupFilterOperation")
        included = create_included.create
        included.resource_name = included_name
        included.asset_group = subdivision.asset_group
        included.type_ = client.enums.ListingGroupFilterTypeEnum.UNIT_INCLUDED
        included.listing_source = client.enums.ListingGroupFilterListingSourceEnum.SHOPPING
        included.parent_listing_group_filter = subdivision_name
        included.case_value.product_custom_attribute.index = (
            client.enums.ListingGroupFilterCustomAttributeIndexEnum.INDEX1
        )
        operations.append(create_included)

    return operations


def verify(nodes: list[ListingNode]) -> dict[int, dict[str, int]]:
    children: dict[str, list[ListingNode]] = defaultdict(list)
    for node in nodes:
        children[node.parent].append(node)
    summary: dict[int, dict[str, int]] = {}
    for asset_group_id in EXPECTED_ASSET_GROUPS:
        group_nodes = [node for node in nodes if node.asset_group_id == asset_group_id]
        gates = [node for node in group_nodes if is_label_exclusion_gate(node, children)]
        unguarded = included_leaves_to_wrap(group_nodes)
        summary[asset_group_id] = {
            "exclusion_gates": len(gates),
            "unguarded_included_leaves": len(unguarded),
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--apply", action="store_true", help="Apply the live Google Ads mutation")
    parser.add_argument("--confirm-customer-id")
    parser.add_argument("--confirm-campaign-id", type=int)
    args = parser.parse_args()

    config = load_config(args.config.expanduser())
    if args.apply and (
        args.confirm_customer_id != config["customer_id"]
        or args.confirm_campaign_id != CAMPAIGN_ID
    ):
        raise SystemExit(
            "Live apply requires exact --confirm-customer-id and --confirm-campaign-id values"
        )

    client = make_client(config)
    asset_groups, nodes = query_state(client, config["customer_id"])
    leaves = included_leaves_to_wrap(nodes)
    print(f"Customer: {config['customer_id']}")
    print(f"Campaign: {CAMPAIGN_NAME} ({CAMPAIGN_ID})")
    for asset_group_id, name in asset_groups.items():
        count = sum(leaf.asset_group_id == asset_group_id for leaf in leaves)
        print(f"- {name} ({asset_group_id}): {count} included branch(es) need the exclusion gate")

    if not leaves:
        print("No changes required.")
        print(json.dumps(verify(nodes), indent=2, sort_keys=True))
        return
    if not args.apply:
        operations = build_operations(client, config["customer_id"], leaves)
        request = client.get_type("MutateAssetGroupListingGroupFiltersRequest")
        request.customer_id = config["customer_id"]
        request.operations.extend(operations)
        request.validate_only = True
        client.get_service(
            "AssetGroupListingGroupFilterService"
        ).mutate_asset_group_listing_group_filters(request=request)
        print(f"Dry run only. Google Ads validated {len(operations)} operations.")
        print("Rerun with guarded apply confirmations to mutate Google Ads.")
        return

    operations = build_operations(client, config["customer_id"], leaves)
    service = client.get_service("AssetGroupListingGroupFilterService")
    response = service.mutate_asset_group_listing_group_filters(
        customer_id=config["customer_id"], operations=operations
    )
    print(f"Applied {len(operations)} listing-group operations.")
    print(f"Mutated resources returned: {len(response.results)}")

    _, verified_nodes = query_state(client, config["customer_id"])
    result = verify(verified_nodes)
    print(json.dumps(result, indent=2, sort_keys=True))
    if any(item["unguarded_included_leaves"] for item in result.values()):
        raise SystemExit("Post-apply verification found an unguarded included branch")
    if any(item["exclusion_gates"] < 1 for item in result.values()):
        raise SystemExit("Post-apply verification did not find an exclusion gate in each asset group")


if __name__ == "__main__":
    try:
        main()
    except GoogleAdsException as exc:
        print(f"Google Ads API request failed: {exc.error.code().name}")
        for error in exc.failure.errors:
            print(f"- {error.message}")
        raise SystemExit(1) from exc

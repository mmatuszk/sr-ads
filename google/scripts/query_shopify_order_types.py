#!/usr/bin/env python3
"""Read Shopify product order types for Google Ads report enrichment."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
SR_AUTOMATION_ROOT = WORKSPACE_ROOT / "sr-automation"
sys.path.insert(0, str(SR_AUTOMATION_ROOT / "src"))

from sr_automation.config import load_config
from sr_automation.shopify import ShopifyGraphQLClient


DEFAULT_CONFIG = SR_AUTOMATION_ROOT / "config" / "automation.yaml"
BATCH_SIZE = 250

PRODUCT_ORDER_TYPE_QUERY = """
query ProductOrderTypes($ids: [ID!]!) {
  nodes(ids: $ids) {
    ... on Product {
      id
      title
      totalInventory
      orderType: metafield(namespace: "order", key: "type") {
        type
        value
      }
    }
  }
}
"""


def normalize_order_type(metafield: dict | None) -> str:
    if not metafield:
        return "unassigned"

    raw_value = metafield.get("value")
    if raw_value is None:
        return "unassigned"

    try:
        parsed = json.loads(str(raw_value))
    except json.JSONDecodeError:
        parsed = raw_value

    if isinstance(parsed, list):
        values = [str(value).strip() for value in parsed if str(value).strip()]
        return ", ".join(values) if values else "unassigned"

    normalized = str(parsed).strip()
    return normalized or "unassigned"


def query_order_types(
    *,
    config_path: Path,
    product_gids: list[str],
) -> dict[str, dict]:
    config = load_config(config_path)
    client = ShopifyGraphQLClient(config.shopify)
    products: dict[str, dict] = {}

    for start in range(0, len(product_gids), BATCH_SIZE):
        batch = product_gids[start : start + BATCH_SIZE]
        data = client.execute(PRODUCT_ORDER_TYPE_QUERY, {"ids": batch})
        for node in data.get("nodes", []):
            if not node:
                continue
            gid = str(node["id"])
            products[gid] = {
                "order_type": normalize_order_type(node.get("orderType")),
                "total_inventory": node.get("totalInventory"),
                "shopify_title": node.get("title"),
            }

    for gid in product_gids:
        products.setdefault(
            gid,
            {
                "order_type": "not_found",
                "total_inventory": None,
                "shopify_title": None,
            },
        )
    return products


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ids-file",
        required=True,
        type=Path,
        help="JSON file containing a list of Shopify Product GIDs.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Destination JSON file for the Shopify lookup result.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"SR Automation config path (default: {DEFAULT_CONFIG}).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_ids = json.loads(args.ids_file.expanduser().read_text(encoding="utf-8"))
    if not isinstance(raw_ids, list):
        raise SystemExit("--ids-file must contain a JSON array.")

    product_gids = list(dict.fromkeys(str(value) for value in raw_ids if value))
    products = query_order_types(
        config_path=args.config.expanduser(),
        product_gids=product_gids,
    )

    payload = {
        "queried_at": datetime.now(UTC).isoformat(),
        "product_count": len(product_gids),
        "products": products,
    }
    args.output.expanduser().parent.mkdir(parents=True, exist_ok=True)
    args.output.expanduser().write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(
        f"Queried {len(product_gids)} Shopify products; "
        f"resolved {sum(item['order_type'] != 'not_found' for item in products.values())}."
    )


if __name__ == "__main__":
    main()

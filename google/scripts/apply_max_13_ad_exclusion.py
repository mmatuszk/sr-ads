#!/usr/bin/env python3
"""Exclude GMC custom_label_1=exclude from the Max-13 asset group.

This guarded entry point reuses the validated Max-2 listing-group workflow with
Max-13's exact campaign and enabled asset-group identities.
"""

from __future__ import annotations

from google.ads.googleads.errors import GoogleAdsException

import apply_max_2_ad_exclusion as workflow


workflow.CAMPAIGN_ID = 23453016844
workflow.CAMPAIGN_NAME = "Performance Max-13"
workflow.EXPECTED_ASSET_GROUPS = {
    6657971628: "Performance Max-13",
}


if __name__ == "__main__":
    try:
        workflow.main()
    except GoogleAdsException as exc:
        print(f"Google Ads API request failed: {exc.error.code().name}")
        for error in exc.failure.errors:
            print(f"- {error.message}")
        raise SystemExit(1) from exc

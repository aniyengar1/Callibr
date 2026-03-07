#!/usr/bin/env python3
"""
Fetch recently resolved Polymarket markets and print their question text.

Requires: pip install requests
"""

from typing import Any

import requests

# API base URL
GAMMA_API_BASE = "https://gamma-api.polymarket.com"


def fetch_resolved_markets(limit: int = 50) -> list[dict[str, Any]]:
    """Fetch recently resolved (closed) markets from the Gamma API."""
    url = f"{GAMMA_API_BASE}/markets"
    params = {
        "closed": "true",
        "limit": limit,
        "order": "closedTime",
        "ascending": "false",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    print("Fetching recently resolved markets...")
    markets = fetch_resolved_markets(limit=50)
    if not markets:
        print("No resolved markets found.")
        return

    print(f"\nFirst {len(markets)} resolved markets (question text):\n")
    for i, market in enumerate(markets, start=1):
        question = market.get("question") or "(no question)"
        print(f"{i}. {question}")


if __name__ == "__main__":
    main()

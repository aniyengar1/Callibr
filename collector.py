import requests
import pandas as pd
import os
import json
from datetime import datetime, timezone
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

OUTPUT_FILE = os.path.expanduser("~/Documents/quantmarkets/market_prices.csv")
KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"
POLYMARKET_BASE = "https://gamma-api.polymarket.com"

# Only skip true MVE combo tickers — no longer skip all KXBTC etc.
# The live endpoint now returns real markets; we filter MVEs via the API param instead.
SKIP_TICKERS_PREFIX = ["KXMVE"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def categorize(question):
    q = question.lower()
    if any(x in q for x in ["trump", "president", "election", "congress", "senate", "biden", "republican", "democrat", "ukraine", "russia", "china", "taiwan", "ceasefire", "tariff", "fed", "federal reserve", "interest rate", "inflation", "gdp"]):
        return "Politics & Macro"
    elif any(x in q for x in ["nhl", "nba", "nfl", "mlb", "fifa", "world cup", "stanley cup", "super bowl", "championship", "soccer", "football", "basketball", "baseball", "hockey", "tennis", "golf"]):
        return "Sports"
    elif any(x in q for x in ["bitcoin", "btc", "eth", "crypto", "ethereum", "solana", "coinbase", "binance"]):
        return "Crypto"
    elif any(x in q for x in ["openai", "gpt", "anthropic", "google", "apple", "microsoft", "nvidia", "stock", "ipo", "earnings"]):
        return "Tech & Markets"
    elif any(x in q for x in ["album", "movie", "gta", "taylor swift", "rihanna", "oscar", "grammy", "celebrity", "convicted", "sentenced", "trial", "weinstein"]):
        return "Entertainment & Legal"
    else:
        return "Other"

def parse_kalshi_price(m):
    """
    Kalshi's API now returns prices as dollar strings (e.g. "0.56") in *_dollars fields.
    The old integer cent fields (yes_bid, last_price) are no longer populated.
    Try dollars fields first, fall back to legacy cent fields.
    """
    # Try new dollar-string fields first
    try:
        last = float(m.get("last_price_dollars") or 0)
        if 0 < last < 1:
            return last
    except (TypeError, ValueError):
        pass

    try:
        bid = float(m.get("yes_bid_dollars") or 0)
        ask = float(m.get("yes_ask_dollars") or 0)
        if bid > 0 and ask > 0:
            mid = (bid + ask) / 2
            if 0 < mid < 1:
                return mid
    except (TypeError, ValueError):
        pass

    # Legacy integer cent fields (kept for backwards compat)
    last_cents = m.get("last_price", 0) or 0
    if last_cents > 0:
        mid = last_cents / 100
        if 0 < mid < 1:
            return mid

    yes_bid_cents = m.get("yes_bid", 0) or 0
    yes_ask_cents = m.get("yes_ask", 0) or 0
    if yes_bid_cents > 0 and yes_ask_cents > 0:
        mid = (yes_bid_cents + yes_ask_cents) / 2 / 100
        if 0 < mid < 1:
            return mid

    return None

def fetch_kalshi_live_markets():
    """Fetch currently open Kalshi markets, excluding MVE combo markets."""
    print("Fetching Kalshi live markets...")
    all_markets = []
    cursor = None

    for page in range(10):
        params = {"limit": 100, "status": "open", "mve_filter": "exclude"}
        if cursor:
            params["cursor"] = cursor
        try:
            r = requests.get(f"{KALSHI_BASE}/markets", params=params, timeout=30)
            if r.status_code != 200:
                print(f"  Kalshi live HTTP {r.status_code}: {r.text[:200]}")
                break
            data = r.json()
            batch = data.get("markets", [])
            all_markets.extend(batch)
            cursor = data.get("cursor")
            if not cursor or len(batch) < 100:
                break
        except Exception as e:
            print(f"  Kalshi live error: {e}")
            break

    rows = []
    timestamp = datetime.now(timezone.utc).isoformat()
    skipped = 0

    for m in all_markets:
        ticker = m.get("ticker", "")
        if not ticker:
            continue
        if any(ticker.startswith(p) for p in SKIP_TICKERS_PREFIX):
            skipped += 1
            continue

        mid_price = parse_kalshi_price(m)
        if mid_price is None:
            skipped += 1
            continue

        event_ticker = m.get("event_ticker", "")
        title = m.get("title", event_ticker)

        rows.append({
            "timestamp": timestamp,
            "source": "kalshi",
            "ticker": ticker,
            "event_ticker": title or event_ticker,
            "category": categorize(title or event_ticker),
            "mid_price": round(mid_price, 4),
            "open_time": m.get("open_time"),
            "close_time": m.get("close_time"),
        })

    print(f"  Kalshi live: {len(rows)} valid markets ({skipped} skipped)")
    return rows

def fetch_kalshi_historical_markets(max_pages=5):
    """
    Fetch recently resolved Kalshi markets from the historical database.
    These have known YES/NO outcomes — valuable for backtesting.
    """
    print("Fetching Kalshi historical markets...")
    all_markets = []
    cursor = None

    for page in range(max_pages):
        params = {"limit": 100, "mve_filter": "exclude"}
        if cursor:
            params["cursor"] = cursor
        try:
            r = requests.get(f"{KALSHI_BASE}/historical/markets", params=params, timeout=30)
            if r.status_code != 200:
                print(f"  Kalshi historical HTTP {r.status_code}: {r.text[:200]}")
                break
            data = r.json()
            batch = data.get("markets", [])
            all_markets.extend(batch)
            cursor = data.get("cursor")
            if not cursor or len(batch) < 100:
                break
        except Exception as e:
            print(f"  Kalshi historical error: {e}")
            break

    rows = []
    timestamp = datetime.now(timezone.utc).isoformat()
    skipped = 0

    for m in all_markets:
        ticker = m.get("ticker", "")
        if not ticker:
            continue
        if any(ticker.startswith(p) for p in SKIP_TICKERS_PREFIX):
            skipped += 1
            continue

        # For historical markets, use last_price as the final settled price
        mid_price = parse_kalshi_price(m)
        if mid_price is None:
            # Historical markets may have settled at 0 or 1 — allow those
            last_dollars = m.get("last_price_dollars")
            last_cents = m.get("last_price", 0) or 0
            if last_dollars is not None:
                try:
                    mid_price = float(last_dollars)
                except (TypeError, ValueError):
                    skipped += 1
                    continue
            elif last_cents in (0, 100):
                mid_price = last_cents / 100
            else:
                skipped += 1
                continue

        event_ticker = m.get("event_ticker", "")
        title = m.get("title", event_ticker)
        result = m.get("result", "")  # "yes" or "no" — outcome of the market

        rows.append({
            "timestamp": timestamp,
            "source": "kalshi_historical",
            "ticker": ticker,
            "event_ticker": title or event_ticker,
            "category": categorize(title or event_ticker),
            "mid_price": round(mid_price, 4),
            "open_time": m.get("open_time"),
            "close_time": m.get("close_time") or m.get("expiration_time"),
        })

    print(f"  Kalshi historical: {len(rows)} valid markets ({skipped} skipped)")
    return rows

def fetch_polymarket_markets():
    print("Fetching Polymarket markets...")
    rows = []
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        offset = 0
        while offset < 500:
            r = requests.get(
                f"{POLYMARKET_BASE}/markets",
                params={"limit": 100, "offset": offset, "active": "true", "closed": "false"},
                timeout=30
            )
            if r.status_code != 200:
                break
            batch = r.json()
            if not batch:
                break
            for m in batch:
                if m.get("groupItemCount", 0) > 0:
                    continue
                outcome_prices = m.get("outcomePrices")
                if not outcome_prices:
                    continue
                try:
                    prices = json.loads(outcome_prices) if isinstance(outcome_prices, str) else outcome_prices
                    yes_price = float(prices[0])
                except:
                    continue
                if yes_price <= 0 or yes_price >= 1:
                    continue
                question = m.get("question", "")[:80]
                rows.append({
                    "timestamp": timestamp,
                    "source": "polymarket",
                    "ticker": m.get("conditionId", ""),
                    "event_ticker": question,
                    "category": categorize(question),
                    "mid_price": round(yes_price, 4),
                    "open_time": m.get("startDateIso"),
                    "close_time": m.get("endDateIso"),
                })
            offset += 100
    except Exception as e:
        print(f"Polymarket error: {e}")

    print(f"  Polymarket: {len(rows)} valid markets")
    return rows

def save_rows(rows):
    if not rows:
        print("No rows to save.")
        return

    df = pd.DataFrame(rows)

    # Save to CSV
    if os.path.exists(OUTPUT_FILE):
        df.to_csv(OUTPUT_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(OUTPUT_FILE, mode="w", header=True, index=False)
    print(f"Saved {len(rows)} rows to CSV")

    # Save to Supabase in batches of 500 to stay within limits
    batch_size = 500
    total_saved = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        try:
            supabase.table("market_prices").insert(batch).execute()
            total_saved += len(batch)
        except Exception as e:
            print(f"Supabase error on batch {i // batch_size + 1}: {e}")
    print(f"Saved {total_saved} rows to Supabase")

def collect():
    print(f"\nRunning collector at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    rows = []
    rows.extend(fetch_kalshi_live_markets())
    rows.extend(fetch_kalshi_historical_markets())
    rows.extend(fetch_polymarket_markets())

    print(f"\nTotal rows collected: {len(rows)}")
    save_rows(rows)

if __name__ == "__main__":
    collect()
import requests
import pandas as pd
import os
import json
from datetime import datetime, timezone, timedelta
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

OUTPUT_FILE = os.path.expanduser("~/Documents/quantmarkets/market_prices.csv")
KALSHI_BASE  = "https://api.elections.kalshi.com/trade-api/v2"
POLY_BASE    = "https://gamma-api.polymarket.com"

SKIP_TICKERS_PREFIX = ["KXMVE"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def categorize(question):
    q = question.lower()
    if any(x in q for x in ["trump","president","election","congress","senate","biden","republican","democrat","ukraine","russia","china","taiwan","ceasefire","tariff","fed","federal reserve","interest rate","inflation","gdp"]):
        return "Politics & Macro"
    elif any(x in q for x in ["nhl","nba","nfl","mlb","fifa","world cup","stanley cup","super bowl","championship","soccer","football","basketball","baseball","hockey","tennis","golf","champions league","premier league","la liga","serie a","bundesliga","ufc","mma","f1","formula"]):
        return "Sports"
    elif any(x in q for x in ["bitcoin","btc","eth","crypto","ethereum","solana","coinbase","binance","xrp","doge"]):
        return "Crypto"
    elif any(x in q for x in ["openai","gpt","anthropic","google","apple","microsoft","nvidia","stock","ipo","earnings"]):
        return "Tech & Markets"
    elif any(x in q for x in ["album","movie","gta","taylor swift","rihanna","oscar","grammy","celebrity","convicted","sentenced","trial","weinstein"]):
        return "Entertainment & Legal"
    else:
        return "Other"

def parse_kalshi_price(m):
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

def fetch_kalshi_short_term():
    """
    Fetch Kalshi markets closing within 30 days, sorted by close_time ascending.
    This captures daily/weekly sports, crypto, and news markets.
    """
    print("Fetching Kalshi short-term markets (closing ≤30 days)...")
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=30)
    all_markets = []
    cursor = None

    for page in range(20):  # up to 2,000 markets
        params = {
            "limit": 100,
            "status": "open",
            "mve_filter": "exclude",
            "max_close_ts": int(cutoff.timestamp()),  # only markets closing before cutoff
        }
        if cursor:
            params["cursor"] = cursor
        try:
            r = requests.get(f"{KALSHI_BASE}/markets", params=params, timeout=30)
            if r.status_code == 429:
                print("  Kalshi rate limited, stopping short-term fetch")
                break
            if r.status_code != 200:
                print(f"  Kalshi short-term HTTP {r.status_code}")
                break
            data = r.json()
            batch = data.get("markets", [])
            all_markets.extend(batch)
            cursor = data.get("cursor")
            if not cursor or len(batch) < 100:
                break
        except Exception as e:
            print(f"  Kalshi short-term error: {e}")
            break

    rows = []
    timestamp = now.isoformat()
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

    print(f"  Kalshi short-term: {len(rows)} markets closing ≤30 days ({skipped} skipped)")
    return rows

def fetch_kalshi_live_markets():
    """Fetch broader Kalshi open markets (long-term included)."""
    print("Fetching Kalshi live markets (all)...")
    all_markets = []
    cursor = None

    for page in range(10):
        params = {"limit": 100, "status": "open", "mve_filter": "exclude"}
        if cursor:
            params["cursor"] = cursor
        try:
            r = requests.get(f"{KALSHI_BASE}/markets", params=params, timeout=30)
            if r.status_code == 429:
                print("  Kalshi rate limited")
                break
            if r.status_code != 200:
                print(f"  Kalshi live HTTP {r.status_code}")
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

    print(f"  Kalshi live (all): {len(rows)} markets ({skipped} skipped)")
    return rows

def fetch_kalshi_historical_markets(max_pages=5):
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
                print(f"  Kalshi historical HTTP {r.status_code}")
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
        mid_price = parse_kalshi_price(m)
        if mid_price is None:
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

    print(f"  Kalshi historical: {len(rows)} markets ({skipped} skipped)")
    return rows

def fetch_polymarket_markets():
    """Fetch Polymarket — sort by end date ascending to get closing-soon markets first."""
    print("Fetching Polymarket markets...")
    rows = []
    timestamp = datetime.now(timezone.utc).isoformat()
    now = datetime.now(timezone.utc)
    cutoff_30d = (now + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        # First pass: markets closing within 30 days
        offset = 0
        while offset < 500:
            r = requests.get(
                f"{POLY_BASE}/markets",
                params={
                    "limit": 100,
                    "offset": offset,
                    "active": "true",
                    "closed": "false",
                    "end_date_max": cutoff_30d,
                    "order": "end_date_min",
                    "ascending": "true",
                },
                timeout=30,
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
                except Exception:
                    continue
                if yes_price <= 0 or yes_price >= 1:
                    continue
                question = m.get("question", "")[:100]
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

        # Second pass: all other active markets
        offset = 0
        while offset < 300:
            r = requests.get(
                f"{POLY_BASE}/markets",
                params={"limit": 100, "offset": offset, "active": "true", "closed": "false"},
                timeout=30,
            )
            if r.status_code != 200:
                break
            batch = r.json()
            if not batch:
                break
            existing_tickers = {row["ticker"] for row in rows}
            for m in batch:
                if m.get("groupItemCount", 0) > 0:
                    continue
                cid = m.get("conditionId", "")
                if cid in existing_tickers:
                    continue
                outcome_prices = m.get("outcomePrices")
                if not outcome_prices:
                    continue
                try:
                    prices = json.loads(outcome_prices) if isinstance(outcome_prices, str) else outcome_prices
                    yes_price = float(prices[0])
                except Exception:
                    continue
                if yes_price <= 0 or yes_price >= 1:
                    continue
                question = m.get("question", "")[:100]
                rows.append({
                    "timestamp": timestamp,
                    "source": "polymarket",
                    "ticker": cid,
                    "event_ticker": question,
                    "category": categorize(question),
                    "mid_price": round(yes_price, 4),
                    "open_time": m.get("startDateIso"),
                    "close_time": m.get("endDateIso"),
                })
                existing_tickers.add(cid)
            offset += 100

    except Exception as e:
        print(f"Polymarket error: {e}")

    print(f"  Polymarket: {len(rows)} valid markets")
    return rows

def save_rows(rows):
    if not rows:
        print("No rows to save.")
        return

    # Deduplicate by ticker+timestamp before saving
    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["ticker", "timestamp"])
    rows = df.to_dict("records")

    if os.path.exists(OUTPUT_FILE):
        df.to_csv(OUTPUT_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(OUTPUT_FILE, mode="w", header=True, index=False)
    print(f"Saved {len(rows)} rows to CSV")

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
    short_term = fetch_kalshi_short_term()
    all_kalshi = fetch_kalshi_live_markets()

    # Merge — short-term first, deduplicate
    seen = {r["ticker"] for r in short_term}
    for r in all_kalshi:
        if r["ticker"] not in seen:
            short_term.append(r)
            seen.add(r["ticker"])
    rows.extend(short_term)

    rows.extend(fetch_kalshi_historical_markets())
    rows.extend(fetch_polymarket_markets())

    print(f"\nTotal rows collected: {len(rows)}")
    save_rows(rows)

if __name__ == "__main__":
    collect()

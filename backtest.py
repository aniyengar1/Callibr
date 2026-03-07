import requests
import pandas as pd
from datetime import datetime, timezone

BASE = "https://api.elections.kalshi.com/trade-api/v2"

def fetch_settled_markets(limit=100):
    r = requests.get(f"{BASE}/historical/markets", 
                     params={"limit": limit, "status": "settled"})
    return r.json()["markets"]

def fetch_candlesticks(series_ticker, market_ticker, open_time, close_time):
    start = int(datetime.fromisoformat(open_time.replace("Z", "+00:00")).timestamp())
    end = int(datetime.fromisoformat(close_time.replace("Z", "+00:00")).timestamp())
    r = requests.get(
        f"{BASE}/series/{series_ticker}/markets/{market_ticker}/candlesticks",
        params={"period_interval": 60, "start_ts": start, "end_ts": end}
    )
    if r.status_code != 200:
        return []
    return r.json().get("candlesticks", [])

def get_series_ticker(market_ticker):
    # series ticker is everything before the last date segment
    parts = market_ticker.split("-")
    # find where the year part starts (e.g. 25, 26)
    for i, p in enumerate(parts):
        if len(p) == 2 and p.isdigit():
            return "-".join(parts[:i+1])
    return "-".join(parts[:-1])

def main():
    print("Fetching settled Kalshi markets...")
    all_markets = []
    cursor = None
    for page in range(50):
        params = {"limit": 100, "status": "settled"}
        if cursor:
            params["cursor"] = cursor
        r = requests.get(f"{BASE}/historical/markets", params=params)
        data = r.json()
        batch = data.get("markets", [])
        all_markets.extend(batch)
        cursor = data.get("cursor")
        print(f"Page {page+1}: {len(all_markets)} total")
        if not cursor or len(batch) < 100:
            break
    markets = all_markets
    print(f"Found {len(markets)} markets")

    rows = []
    for m in markets:
        ticker = m.get("ticker")

        # skip crypto price markets
        # skip short-term crypto price markets (too noisy)
        if not ticker or any(x in ticker for x in ["KXBTCD", "KXBTC-", "KXETH", "KXSOL", "KXXRP", "KXINXU", "KXNASDAQ"]):
            continue
        open_time = m.get("open_time")
        close_time = m.get("close_time")
        expiration_value = m.get("expiration_value")

        if not all([ticker, open_time, close_time, expiration_value]):
            continue

        resolved_yes = expiration_value.lower() == "yes"
        series_ticker = get_series_ticker(ticker)

        candles = fetch_candlesticks(series_ticker, ticker, open_time, close_time)
        if not candles:
            continue

        # opening price = first candle open price (in cents, divide by 100)
        try:
            first = candles[0]["price"]
            last = candles[-1]["price"]
            open_price = (first.get("open") or first.get("mean") or first.get("close")) / 100
            close_price = (last.get("close") or last.get("mean")) / 100
        except:
            continue

        print(f"{ticker} | open: {open_price:.2f} | resolved: {resolved_yes}")

        if open_price < 0.05 or open_price > 0.95:
            continue

        pnl = (1 - open_price) if resolved_yes else -open_price
        rows.append({
            "ticker": ticker,
            "open_price": round(open_price, 3),
            "close_price": round(close_price, 3),
            "resolved_yes": resolved_yes,
            "pnl": round(pnl, 3),
        })

    if not rows:
        print("No trades found.")
        return

    df = pd.DataFrame(rows)
    wins = df[df["resolved_yes"] == True]
    total_pnl = df["pnl"].sum()
    win_rate = len(wins) / len(df) * 100
    sharpe = df["pnl"].mean() / df["pnl"].std() if df["pnl"].std() > 0 else 0

    print(f"\n--- BACKTEST RESULTS ---")
    print(f"Trades:     {len(df)}")
    print(f"Win Rate:   {win_rate:.1f}%")
    print(f"Total PnL:  {total_pnl:.3f} units")
    print(f"Sharpe:     {sharpe:.2f}")

    df['prob_bucket'] = pd.cut(df['open_price'],
                                bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                                labels=['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'])

    print(f"\n--- BY PROBABILITY BUCKET ---")
    bucket_stats = df.groupby('prob_bucket').agg(
        trades=('pnl', 'count'),
        win_rate=('resolved_yes', lambda x: f"{x.mean()*100:.1f}%"),
        avg_pnl=('pnl', lambda x: f"{x.mean():.3f}"),
        total_pnl=('pnl', lambda x: f"{x.sum():.3f}")
    )
    print(bucket_stats.to_string())

    df.to_csv("kalshi_backtest.csv", index=False)
    print(f"\nSaved to kalshi_backtest.csv")

if __name__ == "__main__":
    main()
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from supabase import create_client

st.set_page_config(page_title="QuantMarkets", page_icon="📈", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

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

st.title("📈 QuantMarkets")
st.subheader("Backtesting engine for prediction markets")
st.markdown("---")

@st.cache_data(ttl=300)
def load_data():
    all_rows = []
    offset = 0
    batch_size = 1000
    while True:
        response = supabase.table("market_prices")\
            .select("*")\
            .order("timestamp", desc=False)\
            .range(offset, offset + batch_size - 1)\
            .execute()
        batch = response.data
        if not batch:
            break
        all_rows.extend(batch)
        if len(batch) < batch_size:
            break
        offset += batch_size
    if not all_rows:
        return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    df["mid_price"] = pd.to_numeric(df["mid_price"], errors="coerce")
    df["category"] = df["event_ticker"].apply(categorize)
    return df

df_raw = load_data()

if df_raw.empty:
    st.warning("No data yet.")
    st.stop()

# Split live markets (polymarket + kalshi live) from historical resolved markets
# Historical markets are resolved — prices settled at 0 or 1 — so they skew
# the live dashboard but are valuable for backtesting.
LIVE_SOURCES = ["polymarket", "kalshi"]
df_live_raw = df_raw[df_raw["source"].isin(LIVE_SOURCES)]
df_hist_raw = df_raw[df_raw["source"] == "kalshi_historical"]

# Build market-level summary from live data only
def build_markets_df(df):
    df_first = df.sort_values("timestamp").groupby("ticker").first().reset_index()
    df_latest = df.sort_values("timestamp").groupby("ticker").last().reset_index()
    df_latest = df_latest.rename(columns={"mid_price": "current_price"})
    df_m = df_first.merge(df_latest[["ticker", "current_price"]], on="ticker")
    df_m["price_change"] = (df_m["current_price"] - df_m["mid_price"]).round(4)
    df_m["price_change_pct"] = ((df_m["price_change"] / df_m["mid_price"]) * 100).round(2)
    df_m["days_to_close"] = pd.to_datetime(df_m["close_time"], errors="coerce").dt.tz_localize(None) - pd.Timestamp.now()
    df_m["days_to_close"] = df_m["days_to_close"].dt.days
    return df_m

df_markets = build_markets_df(df_live_raw)

# Sidebar
st.sidebar.title("Filters")
min_prob = st.sidebar.slider("Min opening probability", 0.0, 1.0, 0.05, 0.05)
max_prob = st.sidebar.slider("Max opening probability", 0.0, 1.0, 0.95, 0.05)
categories = ["All"] + sorted(df_markets["category"].unique().tolist())
category_filter = st.sidebar.selectbox("Category", categories)
sort_by = st.sidebar.selectbox("Sort by", ["Opening Price", "Current Price", "Price Change", "Days to Close"])

st.sidebar.markdown("---")
st.sidebar.markdown("### Data Pipeline")
st.sidebar.metric("Total snapshots", len(df_raw))
st.sidebar.metric("Live markets", df_live_raw["ticker"].nunique())
st.sidebar.metric("Historical (resolved)", df_hist_raw["ticker"].nunique())
st.sidebar.metric("Last updated", df_raw["timestamp"].max()[:16])

# Source breakdown
source_counts = df_raw["source"].value_counts()
st.sidebar.markdown("**Sources**")
for src, count in source_counts.items():
    label = {"polymarket": "🟣 Polymarket", "kalshi": "🔵 Kalshi (live)", "kalshi_historical": "📚 Kalshi (resolved)"}.get(src, src)
    st.sidebar.markdown(f"{label}: {df_raw[df_raw['source']==src]['ticker'].nunique()} markets")

# Apply filters
df = df_markets.copy()
df = df[(df["mid_price"] >= min_prob) & (df["mid_price"] <= max_prob)]
if category_filter != "All":
    df = df[df["category"] == category_filter]

sort_map = {"Opening Price": "mid_price", "Current Price": "current_price", "Price Change": "price_change", "Days to Close": "days_to_close"}
df = df.sort_values(sort_map[sort_by], ascending=False).reset_index(drop=True)

# Key metrics row 1
st.markdown("## 📊 Market Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Markets tracked", len(df))
col2.metric("Avg opening price", f"{df['mid_price'].mean():.2%}")
col3.metric("Biggest mover", f"{df['price_change_pct'].abs().max():.1f}%")
col4.metric("Categories", df["category"].nunique())

# Key metrics row 2
col5, col6, col7, col8 = st.columns(4)
col5.metric("Avg current price", f"{df['current_price'].mean():.2%}")
col6.metric("Markets moving up", len(df[df["price_change"] > 0]))
col7.metric("Markets moving down", len(df[df["price_change"] < 0]))
col8.metric("Avg days to close", f"{df['days_to_close'].mean():.0f}d" if df['days_to_close'].notna().any() else "N/A")

st.markdown("---")

# Prediction market specific stats
st.markdown("## 🎯 Prediction Market Intelligence")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown("#### Probability Buckets")
    bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    labels = ["0-10%", "10-20%", "20-30%", "30-40%", "40-50%", "50-60%", "60-70%", "70-80%", "80-90%", "90-100%"]
    df["bucket"] = pd.cut(df["mid_price"], bins=bins, labels=labels)
    bucket_counts = df["bucket"].value_counts().sort_index()
    st.bar_chart(bucket_counts)

with col_b:
    st.markdown("#### Market Sentiment")
    extreme_yes = len(df[df["current_price"] > 0.8])
    extreme_no = len(df[df["current_price"] < 0.2])
    contested = len(df[(df["current_price"] >= 0.4) & (df["current_price"] <= 0.6)])
    sentiment_df = pd.DataFrame({
        "Type": ["Strong YES (>80%)", "Strong NO (<20%)", "Contested (40-60%)"],
        "Count": [extreme_yes, extreme_no, contested]
    })
    fig_s, ax_s = plt.subplots()
    ax_s.bar(sentiment_df["Type"], sentiment_df["Count"], color=["#00C2A8", "#DC2626", "#F59E0B"])
    plt.xticks(rotation=15, ha="right", fontsize=8)
    st.pyplot(fig_s)

with col_c:
    st.markdown("#### Price Drift by Category")
    drift = df.groupby("category")["price_change_pct"].mean().sort_values()
    colors_drift = ["#DC2626" if x < 0 else "#00C2A8" for x in drift.values]
    fig_d, ax_d = plt.subplots()
    ax_d.barh(drift.index, drift.values, color=colors_drift)
    ax_d.axvline(x=0, color="black", linewidth=0.8, linestyle="--")
    ax_d.set_xlabel("Avg Price Change %")
    st.pyplot(fig_d)

st.markdown("---")

# Charts
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Markets by Category")
    cat_counts = df_markets["category"].value_counts()
    colors = ["#6C47FF", "#00C2A8", "#DC2626", "#F59E0B", "#3B82F6"]
    fig, ax = plt.subplots()
    ax.bar(cat_counts.index, cat_counts.values, color=colors[:len(cat_counts)])
    plt.xticks(rotation=20, ha="right")
    ax.set_ylabel("Number of Markets")
    st.pyplot(fig)

with col_right:
    st.subheader("Opening vs Current Price")
    fig2, ax2 = plt.subplots()
    ax2.scatter(df["mid_price"], df["current_price"], alpha=0.5, color="#6C47FF", s=20)
    ax2.plot([0, 1], [0, 1], "r--", linewidth=1, label="No change")
    ax2.set_xlabel("Opening Price")
    ax2.set_ylabel("Current Price")
    ax2.legend()
    st.pyplot(fig2)

st.markdown("---")

st.subheader("🔥 Biggest Price Movers")
top_movers = df_markets.nlargest(10, "price_change_pct")[["event_ticker", "source", "category", "mid_price", "current_price", "price_change_pct"]]
top_movers.columns = ["Market", "Source", "Category", "Opening Price", "Current Price", "Change %"]
st.dataframe(top_movers.reset_index(drop=True), use_container_width=True)

st.markdown("---")

st.subheader("📋 Market Browser")
display_df = df[["source", "category", "event_ticker", "mid_price", "current_price", "price_change_pct", "days_to_close", "close_time"]].copy()
display_df.columns = ["Source", "Category", "Market", "Opening Price", "Current Price", "Change %", "Days Left", "Closes"]
st.dataframe(display_df, use_container_width=True)

st.markdown("---")

# Strategy Backtester
st.markdown("## 🔬 Strategy Backtester")
st.markdown("Define a rule-based strategy and run it against all tracked markets.")

# Let users choose which data to backtest against
bt_source = st.radio(
    "Data source for backtest",
    ["Live markets only (Polymarket + Kalshi)", "Include resolved Kalshi markets (more data)"],
    horizontal=True
)

col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    entry_condition = st.selectbox("Buy YES if opening probability is", ["less than", "greater than", "between"])

with col_s2:
    threshold_1 = st.slider("Threshold 1", 0.05, 0.95, 0.40, 0.05)

with col_s3:
    if entry_condition == "between":
        threshold_2 = st.slider("Threshold 2", 0.05, 0.95, 0.60, 0.05)
    else:
        threshold_2 = None

cat_filter_bt = st.selectbox("Market category", ["All"] + sorted(df_markets["category"].unique().tolist()), key="bt_cat")

if st.button("▶ Run Backtest"):
    # Choose dataset
    if "resolved" in bt_source:
        # Merge live + historical, deduplicate by ticker keeping latest
        combined_raw = pd.concat([df_live_raw, df_hist_raw], ignore_index=True)
        bt_df = build_markets_df(combined_raw)
    else:
        bt_df = df_markets.copy()

    if cat_filter_bt != "All":
        bt_df = bt_df[bt_df["category"] == cat_filter_bt]

    if entry_condition == "less than":
        bt_df = bt_df[bt_df["mid_price"] < threshold_1]
    elif entry_condition == "greater than":
        bt_df = bt_df[bt_df["mid_price"] > threshold_1]
    elif entry_condition == "between":
        bt_df = bt_df[(bt_df["mid_price"] >= threshold_1) & (bt_df["mid_price"] <= threshold_2)]

    if bt_df.empty:
        st.warning("No markets match this strategy.")
    else:
        st.markdown(f"### Results — {len(bt_df)} markets matched")

        r_col1, r_col2, r_col3, r_col4 = st.columns(4)
        avg_open = bt_df["mid_price"].mean()
        avg_current = bt_df["current_price"].mean()
        avg_change = bt_df["price_change_pct"].mean()
        movers_up = len(bt_df[bt_df["price_change"] > 0])

        r_col1.metric("Avg Opening Price", f"{avg_open:.2%}")
        r_col2.metric("Avg Current Price", f"{avg_current:.2%}")
        r_col3.metric("Avg Price Change", f"{avg_change:.1f}%")
        r_col4.metric("Markets Moving Up", movers_up)

        st.markdown("#### Trade List")
        trade_df = bt_df[["event_ticker", "source", "category", "mid_price", "current_price", "price_change_pct", "close_time"]].copy()
        trade_df.columns = ["Market", "Source", "Category", "Entry Price", "Current Price", "Change %", "Closes"]
        st.dataframe(trade_df.reset_index(drop=True), use_container_width=True)

        fig_bt, ax_bt = plt.subplots()
        bt_sorted = bt_df.sort_values("mid_price").reset_index(drop=True)
        bt_sorted["cumulative_change"] = bt_sorted["price_change"].cumsum()
        ax_bt.plot(bt_sorted.index, bt_sorted["cumulative_change"], color="#6C47FF", linewidth=2)
        ax_bt.fill_between(bt_sorted.index, bt_sorted["cumulative_change"], alpha=0.1, color="#6C47FF")
        ax_bt.axhline(y=0, color="black", linewidth=0.8, linestyle="--")
        ax_bt.set_xlabel("Trade #")
        ax_bt.set_ylabel("Cumulative Price Change")
        ax_bt.set_title("Cumulative Performance")
        st.pyplot(fig_bt)

st.markdown("---")

# Smart Bet Recommender
st.markdown("## 💰 Smart Bet Recommender")
st.markdown("Tell us your budget, target return, and risk tolerance — we'll find the best markets for you right now.")

rec_col1, rec_col2, rec_col3 = st.columns(3)

with rec_col1:
    budget = st.number_input("Budget ($)", min_value=10, max_value=100000, value=100, step=10)

with rec_col2:
    target_return = st.number_input("Target profit ($)", min_value=5, max_value=100000, value=50, step=5)

with rec_col3:
    risk_level = st.selectbox("Risk tolerance", ["Low", "Medium", "High"])

rec_category = st.selectbox("Preferred category", ["All"] + sorted(df_markets["category"].unique().tolist()), key="rec_cat")

if st.button("🎯 Find Best Bets"):

    if risk_level == "Low":
        rec_df = df_markets[(df_markets["current_price"] >= 0.65) & (df_markets["current_price"] <= 0.95)]
        risk_label = "Low risk — high probability markets"
    elif risk_level == "Medium":
        rec_df = df_markets[(df_markets["current_price"] >= 0.35) & (df_markets["current_price"] <= 0.65)]
        risk_label = "Medium risk — contested markets"
    else:
        rec_df = df_markets[(df_markets["current_price"] >= 0.05) & (df_markets["current_price"] <= 0.35)]
        risk_label = "High risk — contrarian markets"

    if rec_category != "All":
        rec_df = rec_df[rec_df["category"] == rec_category]

    if rec_df.empty:
        st.warning("No markets match your criteria. Try adjusting your filters.")
    else:
        rec_df = rec_df.copy()
        rec_df["payout_if_yes"] = (1 / rec_df["current_price"]).round(2)

        # Sort by best probability first
        rec_df = rec_df.sort_values("current_price", ascending=False).reset_index(drop=True)

        # Allocate budget evenly across top markets
        max_bets = min(10, len(rec_df))
        bet_per_market = round(budget / max_bets, 2)
        rec_df = rec_df.head(max_bets)
        rec_df["bet_amount"] = bet_per_market
        rec_df["potential_profit"] = ((rec_df["payout_if_yes"] - 1) * rec_df["bet_amount"]).round(2)
        rec_df["pct_of_budget"] = ((rec_df["bet_amount"] / budget) * 100).round(1)

        # Build direct links for Polymarket markets
        # Polymarket ticker = conditionId; URL format: polymarket.com/event/<conditionId>
        def make_link(row):
            if row["source"] == "polymarket":
                return f"https://polymarket.com/event/{row['ticker']}"
            elif row["source"] == "kalshi":
                return f"https://kalshi.com/markets/{row['ticker']}"
            return ""

        rec_df["link"] = rec_df.apply(make_link, axis=1)

        st.markdown(f"### Top Bets — {risk_label}")

        s_col1, s_col2, s_col3 = st.columns(3)
        s_col1.metric("Markets found", len(rec_df))
        s_col2.metric("Avg probability", f"{rec_df['current_price'].mean():.2%}")
        s_col3.metric("Avg payout per $1", f"{rec_df['payout_if_yes'].mean():.2f}x")

        st.markdown("#### Recommended Bets")
        bet_display = rec_df[[
            "event_ticker", "source", "category", "current_price",
            "payout_if_yes", "bet_amount", "potential_profit", "close_time", "link"
        ]].copy()
        bet_display.columns = [
            "Market", "Source", "Category", "Current Probability",
            "Payout per $1", "Bet Amount ($)", "Potential Profit ($)", "Closes", "🔗 Place Bet"
        ]

        # Render as HTML table so links are clickable
        def render_link(url):
            if url:
                return f'<a href="{url}" target="_blank">Place Bet →</a>'
            return ""

        bet_html = bet_display.copy()
        bet_html["🔗 Place Bet"] = bet_html["🔗 Place Bet"].apply(render_link)
        st.write(bet_html.to_html(escape=False, index=False), unsafe_allow_html=True)

        total_bet = rec_df["bet_amount"].sum()
        total_profit = rec_df["potential_profit"].sum()
        st.markdown("---")
        p_col1, p_col2, p_col3 = st.columns(3)
        p_col1.metric("Total capital deployed", f"${total_bet:.2f}")
        p_col2.metric("% of budget used", f"{(total_bet/budget*100):.1f}%")
        p_col3.metric("Total potential profit", f"${total_profit:.2f}")
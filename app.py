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

df_first = df_raw.sort_values("timestamp").groupby("ticker").first().reset_index()
df_latest = df_raw.sort_values("timestamp").groupby("ticker").last().reset_index()
df_latest = df_latest.rename(columns={"mid_price": "current_price"})
df_markets = df_first.merge(df_latest[["ticker", "current_price"]], on="ticker")
df_markets["price_change"] = (df_markets["current_price"] - df_markets["mid_price"]).round(4)
df_markets["price_change_pct"] = ((df_markets["price_change"] / df_markets["mid_price"]) * 100).round(2)
df_markets["days_to_close"] = pd.to_datetime(df_markets["close_time"], errors="coerce").dt.tz_localize(None) - pd.Timestamp.now()
df_markets["days_to_close"] = df_markets["days_to_close"].dt.days

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
st.sidebar.metric("Unique markets", df_raw["ticker"].nunique())
st.sidebar.metric("Last updated", df_raw["timestamp"].max()[:16])

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
top_movers = df_markets.nlargest(10, "price_change_pct")[["event_ticker", "category", "mid_price", "current_price", "price_change_pct"]]
top_movers.columns = ["Market", "Category", "Opening Price", "Current Price", "Change %"]
st.dataframe(top_movers.reset_index(drop=True), use_container_width=True)

st.markdown("---")

st.subheader("📋 Market Browser")
display_df = df[["category", "event_ticker", "mid_price", "current_price", "price_change_pct", "days_to_close", "close_time"]].copy()
display_df.columns = ["Category", "Market", "Opening Price", "Current Price", "Change %", "Days Left", "Closes"]
st.dataframe(display_df, use_container_width=True)

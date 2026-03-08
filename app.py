import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from supabase import create_client

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

st.set_page_config(page_title="QuantMarkets", page_icon="📈", layout="wide")
st.title("📈 QuantMarkets")
st.subheader("Backtesting engine for prediction markets")
st.markdown("---")

@st.cache_data(ttl=3600)
def load_data():
    response = supabase.table("market_prices").select("*").execute()
    df = pd.DataFrame(response.data)
    if df.empty:
        return df
    df["mid_price"] = pd.to_numeric(df["mid_price"], errors="coerce")
    df["category"] = df["event_ticker"].apply(categorize)
    return df

df_raw = load_data()

if df_raw.empty:
    st.warning("No data yet.")
    st.stop()

# Get first and latest snapshot per market
df_first = df_raw.sort_values("timestamp").groupby("ticker").first().reset_index()
df_latest = df_raw.sort_values("timestamp").groupby("ticker").last().reset_index()
df_latest = df_latest.rename(columns={"mid_price": "current_price"})
df_markets = df_first.merge(df_latest[["ticker", "current_price"]], on="ticker")
df_markets["price_change"] = (df_markets["current_price"] - df_markets["mid_price"]).round(4)
df_markets["price_change_pct"] = ((df_markets["price_change"] / df_markets["mid_price"]) * 100).round(2)

# Sidebar
st.sidebar.title("Filters")
min_prob = st.sidebar.slider("Min opening probability", 0.0, 1.0, 0.05, 0.05)
max_prob = st.sidebar.slider("Max opening probability", 0.0, 1.0, 0.95, 0.05)
categories = ["All"] + sorted(df_markets["category"].unique().tolist())
category_filter = st.sidebar.selectbox("Category", categories)
sort_by = st.sidebar.selectbox("Sort by", ["Opening Price", "Current Price", "Price Change", "Close Date"])

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

sort_map = {"Opening Price": "mid_price", "Current Price": "current_price", "Price Change": "price_change", "Close Date": "close_time"}
df = df.sort_values(sort_map[sort_by], ascending=False).reset_index(drop=True)

# Metrics
st.markdown("## 📊 Market Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Markets tracked", len(df))
col2.metric("Avg opening price", f"{df['mid_price'].mean():.2%}")
col3.metric("Biggest mover", f"{df['price_change_pct'].abs().max():.1f}%")
col4.metric("Categories", df["category"].nunique())
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
    st.subheader("Price Distribution")
    fig2, ax2 = plt.subplots()
    for cat in df_markets["category"].unique():
        subset = df_markets[df_markets["category"] == cat]["mid_price"]
        ax2.hist(subset, bins=15, alpha=0.6, label=cat)
    ax2.set_xlabel("Opening Price")
    ax2.set_ylabel("Count")
    ax2.legend(fontsize=7)
    st.pyplot(fig2)

st.markdown("---")

# Top movers
st.subheader("🔥 Biggest Price Movers")
top_movers = df_markets.nlargest(10, "price_change_pct")[["event_ticker", "category", "mid_price", "current_price", "price_change_pct"]]
top_movers.columns = ["Market", "Category", "Opening Price", "Current Price", "Change %"]
st.dataframe(top_movers.reset_index(drop=True), use_container_width=True)

st.markdown("---")

# Market browser
st.subheader("📋 Market Browser")
display_df = df[["category", "event_ticker", "mid_price", "current_price", "price_change_pct", "close_time"]].copy()
display_df.columns = ["Category", "Market", "Opening Price", "Current Price", "Change %", "Closes"]
st.dataframe(display_df, use_container_width=True)

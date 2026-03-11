import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from supabase import create_client

st.set_page_config(page_title="QuantMarkets", page_icon="📈", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── colours & labels per source ───────────────────────────────────────────────
SOURCE_COLORS = {
    "polymarket":        "#8B5CF6",
    "kalshi":            "#3B82F6",
    "kalshi_historical": "#6B7280",
}
SOURCE_LABELS = {
    "polymarket":        "🟣 Polymarket",
    "kalshi":            "🔵 Kalshi (live)",
    "kalshi_historical": "📚 Kalshi (resolved)",
}

def categorize(question):
    q = question.lower()
    if any(x in q for x in ["trump", "president", "election", "congress", "senate", "biden",
                              "republican", "democrat", "ukraine", "russia", "china", "taiwan",
                              "ceasefire", "tariff", "fed", "federal reserve", "interest rate",
                              "inflation", "gdp"]):
        return "Politics & Macro"
    elif any(x in q for x in ["nhl", "nba", "nfl", "mlb", "fifa", "world cup", "stanley cup",
                                "super bowl", "championship", "soccer", "football", "basketball",
                                "baseball", "hockey", "tennis", "golf"]):
        return "Sports"
    elif any(x in q for x in ["bitcoin", "btc", "eth", "crypto", "ethereum", "solana",
                                "coinbase", "binance"]):
        return "Crypto"
    elif any(x in q for x in ["openai", "gpt", "anthropic", "google", "apple", "microsoft",
                                "nvidia", "stock", "ipo", "earnings"]):
        return "Tech & Markets"
    elif any(x in q for x in ["album", "movie", "gta", "taylor swift", "rihanna", "oscar",
                                "grammy", "celebrity", "convicted", "sentenced", "trial",
                                "weinstein"]):
        return "Entertainment & Legal"
    else:
        return "Other"

# ── data loading ──────────────────────────────────────────────────────────────
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
    df["category"]  = df["event_ticker"].apply(categorize)
    return df

def build_markets_df(df):
    """Collapse raw snapshots: first snapshot = entry price, last = current price."""
    df_first  = df.sort_values("timestamp").groupby("ticker").first().reset_index()
    df_latest = df.sort_values("timestamp").groupby("ticker").last().reset_index()
    df_latest = df_latest.rename(columns={"mid_price": "current_price"})
    df_m = df_first.merge(df_latest[["ticker", "current_price"]], on="ticker")
    df_m["price_change"]     = (df_m["current_price"] - df_m["mid_price"]).round(4)
    df_m["price_change_pct"] = ((df_m["price_change"] / df_m["mid_price"]) * 100).round(2)
    df_m["days_to_close"]    = (
        pd.to_datetime(df_m["close_time"], errors="coerce").dt.tz_localize(None)
        - pd.Timestamp.now()
    ).dt.days
    return df_m

df_raw = load_data()
if df_raw.empty:
    st.warning("No data yet.")
    st.stop()

# Per-source raw slices
df_poly_raw   = df_raw[df_raw["source"] == "polymarket"]
df_kalshi_raw = df_raw[df_raw["source"] == "kalshi"]
df_hist_raw   = df_raw[df_raw["source"] == "kalshi_historical"]
df_live_raw   = df_raw[df_raw["source"].isin(["polymarket", "kalshi"])]

# Per-source market-level summaries
df_poly_markets   = build_markets_df(df_poly_raw)   if not df_poly_raw.empty   else pd.DataFrame()
df_kalshi_markets = build_markets_df(df_kalshi_raw)  if not df_kalshi_raw.empty  else pd.DataFrame()
df_hist_markets   = build_markets_df(df_hist_raw)   if not df_hist_raw.empty   else pd.DataFrame()
df_markets        = build_markets_df(df_live_raw)    # combined live

# ── sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("Filters")
min_prob        = st.sidebar.slider("Min opening probability", 0.0, 1.0, 0.05, 0.05)
max_prob        = st.sidebar.slider("Max opening probability", 0.0, 1.0, 0.95, 0.05)
categories      = ["All"] + sorted(df_markets["category"].unique().tolist())
category_filter = st.sidebar.selectbox("Category", categories)
sort_by         = st.sidebar.selectbox("Sort by", ["Opening Price", "Current Price",
                                                    "Price Change", "Days to Close"])
st.sidebar.markdown("---")
st.sidebar.markdown("### Data Pipeline")
st.sidebar.metric("Total snapshots", len(df_raw))
st.sidebar.metric("Last updated",    df_raw["timestamp"].max()[:16])
st.sidebar.markdown("**Sources**")
for src in ["polymarket", "kalshi", "kalshi_historical"]:
    n = df_raw[df_raw["source"] == src]["ticker"].nunique()
    st.sidebar.markdown(f"{SOURCE_LABELS[src]}: **{n}** markets")

# Apply sidebar filters to combined live df
df = df_markets.copy()
df = df[(df["mid_price"] >= min_prob) & (df["mid_price"] <= max_prob)]
if category_filter != "All":
    df = df[df["category"] == category_filter]
sort_map = {"Opening Price": "mid_price", "Current Price": "current_price",
            "Price Change": "price_change", "Days to Close": "days_to_close"}
df = df.sort_values(sort_map[sort_by], ascending=False).reset_index(drop=True)

# ── Market Overview ───────────────────────────────────────────────────────────
st.markdown("## 📊 Market Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Markets tracked",   len(df))
c2.metric("Avg opening price", f"{df['mid_price'].mean():.2%}")
c3.metric("Biggest mover",     f"{df['price_change_pct'].abs().max():.1f}%")
c4.metric("Categories",        df["category"].nunique())
c5, c6, c7, c8 = st.columns(4)
c5.metric("Avg current price",   f"{df['current_price'].mean():.2%}")
c6.metric("Markets moving up",   len(df[df["price_change"] > 0]))
c7.metric("Markets moving down", len(df[df["price_change"] < 0]))
c8.metric("Avg days to close",
          f"{df['days_to_close'].mean():.0f}d" if df["days_to_close"].notna().any() else "N/A")

st.markdown("---")

# ── SOURCE COMPARISON ─────────────────────────────────────────────────────────
st.markdown("## 🔀 Polymarket vs Kalshi — Live Markets")

def render_source_panel(col, df_src, label, color):
    with col:
        st.markdown(f"#### {label}")
        if df_src.empty:
            st.info("No data yet.")
            return
        m1, m2, m3 = st.columns(3)
        m1.metric("Markets",        len(df_src))
        m2.metric("Avg probability", f"{df_src['current_price'].mean():.2%}")
        m3.metric("Moving up",       len(df_src[df_src["price_change"] > 0]))

        # Probability distribution
        bins    = [0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.0]
        blabels = ["0-10%","10-20%","20-30%","30-40%","40-50%",
                   "50-60%","60-70%","70-80%","80-90%","90-100%"]
        buckets = pd.cut(df_src["current_price"], bins=bins,
                         labels=blabels).value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(5, 2.8))
        ax.bar(buckets.index, buckets.values, color=color, alpha=0.85)
        ax.set_title("Probability Distribution", fontsize=9)
        ax.set_ylabel("# Markets", fontsize=8)
        plt.xticks(rotation=45, ha="right", fontsize=7)
        plt.tight_layout()
        st.pyplot(fig); plt.close(fig)

        # Category breakdown
        cats = df_src["category"].value_counts()
        fig2, ax2 = plt.subplots(figsize=(5, 2.8))
        ax2.barh(cats.index, cats.values, color=color, alpha=0.85)
        ax2.set_title("Markets by Category", fontsize=9)
        ax2.set_xlabel("# Markets", fontsize=8)
        plt.tight_layout()
        st.pyplot(fig2); plt.close(fig2)

        # Price drift by category
        if "price_change_pct" in df_src.columns:
            drift = df_src.groupby("category")["price_change_pct"].mean().sort_values()
            drift_colors = ["#DC2626" if x < 0 else "#00C2A8" for x in drift.values]
            fig3, ax3 = plt.subplots(figsize=(5, 2.8))
            ax3.barh(drift.index, drift.values, color=drift_colors)
            ax3.axvline(x=0, color="black", linewidth=0.8, linestyle="--")
            ax3.set_title("Avg Price Drift by Category", fontsize=9)
            ax3.set_xlabel("Avg Change %", fontsize=8)
            plt.tight_layout()
            st.pyplot(fig3); plt.close(fig3)

left_col, right_col = st.columns(2)
render_source_panel(left_col,  df_poly_markets,   "🟣 Polymarket",    SOURCE_COLORS["polymarket"])
render_source_panel(right_col, df_kalshi_markets, "🔵 Kalshi (live)", SOURCE_COLORS["kalshi"])

st.markdown("---")

# ── Opening vs Current — colour by source ────────────────────────────────────
st.subheader("Opening vs Current Price — by Source")
fig_sc, ax_sc = plt.subplots(figsize=(7, 4))
for src in ["polymarket", "kalshi"]:
    sub = df[df["source"] == src] if "source" in df.columns else pd.DataFrame()
    if not sub.empty:
        ax_sc.scatter(sub["mid_price"], sub["current_price"],
                      alpha=0.45, s=18,
                      color=SOURCE_COLORS[src], label=SOURCE_LABELS[src])
ax_sc.plot([0, 1], [0, 1], "r--", linewidth=1, label="No change")
ax_sc.set_xlabel("Opening Price"); ax_sc.set_ylabel("Current Price")
ax_sc.legend(fontsize=8)
plt.tight_layout()
st.pyplot(fig_sc); plt.close(fig_sc)

st.markdown("---")

# ── KALSHI RESOLVED ───────────────────────────────────────────────────────────
st.markdown("## 📚 Kalshi Resolved Markets")
if df_hist_markets.empty:
    st.info("No resolved Kalshi markets collected yet — check back after the next collector run.")
else:
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Resolved markets",     len(df_hist_markets))
    h2.metric("Settled YES (≥0.9)",   len(df_hist_markets[df_hist_markets["current_price"] >= 0.9]))
    h3.metric("Settled NO (≤0.1)",    len(df_hist_markets[df_hist_markets["current_price"] <= 0.1]))
    h4.metric("Avg settlement price", f"{df_hist_markets['current_price'].mean():.2%}")

    hc1, hc2 = st.columns(2)
    with hc1:
        bins    = [0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.0]
        blabels = ["0-10%","10-20%","20-30%","30-40%","40-50%",
                   "50-60%","60-70%","70-80%","80-90%","90-100%"]
        hbuckets = pd.cut(df_hist_markets["current_price"], bins=bins,
                          labels=blabels).value_counts().sort_index()
        fig_h, ax_h = plt.subplots(figsize=(5, 3))
        ax_h.bar(hbuckets.index, hbuckets.values,
                 color=SOURCE_COLORS["kalshi_historical"], alpha=0.85)
        ax_h.set_title("Settlement Price Distribution", fontsize=9)
        ax_h.set_ylabel("# Markets")
        plt.xticks(rotation=45, ha="right", fontsize=7)
        plt.tight_layout()
        st.pyplot(fig_h); plt.close(fig_h)

    with hc2:
        hcats = df_hist_markets["category"].value_counts()
        fig_hc, ax_hc = plt.subplots(figsize=(5, 3))
        ax_hc.barh(hcats.index, hcats.values,
                   color=SOURCE_COLORS["kalshi_historical"], alpha=0.85)
        ax_hc.set_title("Resolved Markets by Category", fontsize=9)
        ax_hc.set_xlabel("# Markets")
        plt.tight_layout()
        st.pyplot(fig_hc); plt.close(fig_hc)

    st.markdown("##### Most Recently Resolved")
    hist_display = df_hist_markets.sort_values("close_time", ascending=False).head(20)[
        ["event_ticker", "category", "mid_price", "current_price", "close_time"]
    ].copy()
    hist_display.columns = ["Market", "Category", "Entry Price", "Settlement Price", "Closed"]
    st.dataframe(hist_display.reset_index(drop=True), use_container_width=True)

st.markdown("---")

# ── Prediction Market Intelligence ───────────────────────────────────────────
st.markdown("## 🎯 Prediction Market Intelligence")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown("#### Probability Buckets")
    bins   = [0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.0]
    labels = ["0-10%","10-20%","20-30%","30-40%","40-50%",
              "50-60%","60-70%","70-80%","80-90%","90-100%"]
    df["bucket"] = pd.cut(df["mid_price"], bins=bins, labels=labels)
    st.bar_chart(df["bucket"].value_counts().sort_index())

with col_b:
    st.markdown("#### Market Sentiment")
    fig_s, ax_s = plt.subplots()
    ax_s.bar(["Strong YES (>80%)", "Strong NO (<20%)", "Contested (40-60%)"],
             [len(df[df["current_price"] > 0.8]),
              len(df[df["current_price"] < 0.2]),
              len(df[(df["current_price"] >= 0.4) & (df["current_price"] <= 0.6)])],
             color=["#00C2A8", "#DC2626", "#F59E0B"])
    plt.xticks(rotation=15, ha="right", fontsize=8)
    st.pyplot(fig_s); plt.close(fig_s)

with col_c:
    st.markdown("#### Price Drift by Category")
    drift = df.groupby("category")["price_change_pct"].mean().sort_values()
    fig_d, ax_d = plt.subplots()
    ax_d.barh(drift.index, drift.values,
              color=["#DC2626" if x < 0 else "#00C2A8" for x in drift.values])
    ax_d.axvline(x=0, color="black", linewidth=0.8, linestyle="--")
    ax_d.set_xlabel("Avg Price Change %")
    st.pyplot(fig_d); plt.close(fig_d)

st.markdown("---")

# ── Biggest movers ────────────────────────────────────────────────────────────
st.subheader("🔥 Biggest Price Movers")
top_movers = df_markets.nlargest(10, "price_change_pct")[
    ["event_ticker", "source", "category", "mid_price", "current_price", "price_change_pct"]
].copy()
top_movers["source"] = top_movers["source"].map(SOURCE_LABELS).fillna(top_movers["source"])
top_movers.columns   = ["Market", "Source", "Category", "Opening Price", "Current Price", "Change %"]
st.dataframe(top_movers.reset_index(drop=True), use_container_width=True)

st.markdown("---")

# ── Market Browser ────────────────────────────────────────────────────────────
st.subheader("📋 Market Browser")
display_df = df[["source", "category", "event_ticker", "mid_price",
                  "current_price", "price_change_pct", "days_to_close", "close_time"]].copy()
display_df["source"] = display_df["source"].map(SOURCE_LABELS).fillna(display_df["source"])
display_df.columns   = ["Source", "Category", "Market", "Opening Price",
                         "Current Price", "Change %", "Days Left", "Closes"]
st.dataframe(display_df, use_container_width=True)

st.markdown("---")

# ── Strategy Backtester ───────────────────────────────────────────────────────
st.markdown("## 🔬 Strategy Backtester")
st.markdown("Define a rule-based strategy and run it against tracked markets.")

bt_source = st.radio(
    "Data source",
    ["Live (Polymarket + Kalshi)", "Polymarket only", "Kalshi live only",
     "Include resolved Kalshi (more data)"],
    horizontal=True
)

col_s1, col_s2, col_s3 = st.columns(3)
with col_s1:
    entry_condition = st.selectbox("Buy YES if opening probability is",
                                   ["less than", "greater than", "between"])
with col_s2:
    threshold_1 = st.slider("Threshold 1", 0.05, 0.95, 0.40, 0.05)
with col_s3:
    threshold_2 = st.slider("Threshold 2", 0.05, 0.95, 0.60, 0.05) \
        if entry_condition == "between" else None

cat_filter_bt = st.selectbox("Market category",
                              ["All"] + sorted(df_markets["category"].unique().tolist()),
                              key="bt_cat")

if st.button("▶ Run Backtest"):
    if "Polymarket only" in bt_source:
        bt_base = df_poly_markets.copy()
    elif "Kalshi live only" in bt_source:
        bt_base = df_kalshi_markets.copy()
    elif "resolved" in bt_source:
        bt_base = build_markets_df(pd.concat([df_live_raw, df_hist_raw], ignore_index=True))
    else:
        bt_base = df_markets.copy()

    if cat_filter_bt != "All":
        bt_base = bt_base[bt_base["category"] == cat_filter_bt]

    if entry_condition == "less than":
        bt_df = bt_base[bt_base["mid_price"] < threshold_1]
    elif entry_condition == "greater than":
        bt_df = bt_base[bt_base["mid_price"] > threshold_1]
    else:
        bt_df = bt_base[(bt_base["mid_price"] >= threshold_1) &
                        (bt_base["mid_price"] <= threshold_2)]

    if bt_df.empty:
        st.warning("No markets match this strategy.")
    else:
        st.markdown(f"### Results — {len(bt_df)} markets matched")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Avg Opening Price", f"{bt_df['mid_price'].mean():.2%}")
        r2.metric("Avg Current Price", f"{bt_df['current_price'].mean():.2%}")
        r3.metric("Avg Price Change",  f"{bt_df['price_change_pct'].mean():.1f}%")
        r4.metric("Markets Moving Up", len(bt_df[bt_df["price_change"] > 0]))

        trade_df = bt_df[["event_ticker", "source", "category", "mid_price",
                           "current_price", "price_change_pct", "close_time"]].copy()
        trade_df["source"] = trade_df["source"].map(SOURCE_LABELS).fillna(trade_df["source"])
        trade_df.columns   = ["Market", "Source", "Category", "Entry Price",
                               "Current Price", "Change %", "Closes"]
        st.dataframe(trade_df.reset_index(drop=True), use_container_width=True)

        bt_sorted = bt_df.sort_values("mid_price").reset_index(drop=True)
        bt_sorted["cumulative_change"] = bt_sorted["price_change"].cumsum()
        fig_bt, ax_bt = plt.subplots()
        ax_bt.plot(bt_sorted.index, bt_sorted["cumulative_change"], color="#6C47FF", linewidth=2)
        ax_bt.fill_between(bt_sorted.index, bt_sorted["cumulative_change"],
                            alpha=0.1, color="#6C47FF")
        ax_bt.axhline(y=0, color="black", linewidth=0.8, linestyle="--")
        ax_bt.set_xlabel("Trade #"); ax_bt.set_ylabel("Cumulative Price Change")
        ax_bt.set_title("Cumulative Performance")
        st.pyplot(fig_bt); plt.close(fig_bt)

st.markdown("---")

# ── Smart Bet Recommender ─────────────────────────────────────────────────────
st.markdown("## 💰 Smart Bet Recommender")
st.markdown("Tell us your budget, target return, and risk tolerance — we'll find the best markets for you right now.")

rc1, rc2, rc3 = st.columns(3)
with rc1:
    budget = st.number_input("Budget ($)", min_value=10, max_value=100000, value=100, step=10)
with rc2:
    target_return = st.number_input("Target profit ($)", min_value=5, max_value=100000, value=50, step=5)
with rc3:
    risk_level = st.selectbox("Risk tolerance", ["Low", "Medium", "High"])

rec_source   = st.selectbox("Source",
                             ["All (Polymarket + Kalshi)", "Polymarket only", "Kalshi only"],
                             key="rec_src")
rec_category = st.selectbox("Preferred category",
                             ["All"] + sorted(df_markets["category"].unique().tolist()),
                             key="rec_cat")

if st.button("🎯 Find Best Bets"):
    if risk_level == "Low":
        rec_df     = df_markets[(df_markets["current_price"] >= 0.65) & (df_markets["current_price"] <= 0.95)]
        risk_label = "Low risk — high probability markets"
    elif risk_level == "Medium":
        rec_df     = df_markets[(df_markets["current_price"] >= 0.35) & (df_markets["current_price"] <= 0.65)]
        risk_label = "Medium risk — contested markets"
    else:
        rec_df     = df_markets[(df_markets["current_price"] >= 0.05) & (df_markets["current_price"] <= 0.35)]
        risk_label = "High risk — contrarian markets"

    if "Polymarket only" in rec_source:
        rec_df = rec_df[rec_df["source"] == "polymarket"]
    elif "Kalshi only" in rec_source:
        rec_df = rec_df[rec_df["source"] == "kalshi"]
    if rec_category != "All":
        rec_df = rec_df[rec_df["category"] == rec_category]

    if rec_df.empty:
        st.warning("No markets match your criteria. Try adjusting your filters.")
    else:
        rec_df = rec_df.copy()
        rec_df["payout_if_yes"] = (1 / rec_df["current_price"]).round(2)
        rec_df = rec_df.sort_values("current_price", ascending=False).reset_index(drop=True)

        max_bets       = min(10, len(rec_df))
        bet_per_market = round(budget / max_bets, 2)
        rec_df         = rec_df.head(max_bets)
        rec_df["bet_amount"]       = bet_per_market
        rec_df["potential_profit"] = ((rec_df["payout_if_yes"] - 1) * rec_df["bet_amount"]).round(2)

        def make_link(row):
            if row["source"] == "polymarket":
                return f'<a href="https://polymarket.com/event/{row["ticker"]}" target="_blank">Place Bet →</a>'
            elif row["source"] == "kalshi":
                return f'<a href="https://kalshi.com/markets/{row["ticker"]}" target="_blank">Place Bet →</a>'
            return ""
        rec_df["link"] = rec_df.apply(make_link, axis=1)

        st.markdown(f"### Top Bets — {risk_label}")
        s1, s2, s3 = st.columns(3)
        s1.metric("Markets found",     len(rec_df))
        s2.metric("Avg probability",   f"{rec_df['current_price'].mean():.2%}")
        s3.metric("Avg payout per $1", f"{rec_df['payout_if_yes'].mean():.2f}x")

        bet_display = rec_df[["event_ticker", "source", "category", "current_price",
                               "payout_if_yes", "bet_amount", "potential_profit",
                               "close_time", "link"]].copy()
        bet_display["source"] = bet_display["source"].map(SOURCE_LABELS).fillna(bet_display["source"])
        bet_display.columns   = ["Market", "Source", "Category", "Current Probability",
                                  "Payout per $1", "Bet Amount ($)", "Potential Profit ($)",
                                  "Closes", "🔗 Place Bet"]
        st.write(bet_display.to_html(escape=False, index=False), unsafe_allow_html=True)

        total_bet    = rec_df["bet_amount"].sum()
        total_profit = rec_df["potential_profit"].sum()
        st.markdown("---")
        p1, p2, p3 = st.columns(3)
        p1.metric("Total capital deployed", f"${total_bet:.2f}")
        p2.metric("% of budget used",       f"{(total_bet/budget*100):.1f}%")
        p3.metric("Total potential profit", f"${total_profit:.2f}")

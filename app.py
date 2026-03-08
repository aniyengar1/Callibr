import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="QuantMarkets", page_icon="📈", layout="wide")

# Header
st.title("📈 QuantMarkets")
st.subheader("Backtesting engine for prediction markets")
st.markdown("---")

# Sidebar controls
st.sidebar.title("Strategy Settings")
min_prob = st.sidebar.slider("Minimum opening probability", 0.0, 1.0, 0.05, 0.05)
max_prob = st.sidebar.slider("Maximum opening probability", 0.0, 1.0, 0.95, 0.05)
market_filter = st.sidebar.selectbox("Market type", ["All", "Political", "Sports", "Economic"])

# Hardcoded real Kalshi data
data = [
    {"ticker": "KXTARIFFLENGTHMEX-25-MAR09", "type": "Political", "open_price": 0.67, "resolved_yes": True, "pnl": 0.33},
    {"ticker": "KXDJTJOINTSESSION-25MAR04-PB", "type": "Political", "open_price": 0.25, "resolved_yes": True, "pnl": 0.75},
    {"ticker": "KXDJTJOINTSESSION-25MAR04-IVANKA", "type": "Political", "open_price": 0.13, "resolved_yes": False, "pnl": -0.13},
    {"ticker": "KXDJTJOINTSESSION-25MAR04-EPSTEIN", "type": "Political", "open_price": 0.06, "resolved_yes": False, "pnl": -0.06},
    {"ticker": "KXDJTJOINTSESSION-25MAR04-VZ", "type": "Political", "open_price": 0.75, "resolved_yes": True, "pnl": 0.25},
    {"ticker": "KXDJTJOINTSESSION-25MAR04-VP", "type": "Political", "open_price": 0.75, "resolved_yes": True, "pnl": 0.25},
    {"ticker": "KXDJTJOINTSESSION-25MAR04-UKRAINE", "type": "Political", "open_price": 0.90, "resolved_yes": True, "pnl": 0.10},
    {"ticker": "KXDJTJOINTSESSION-25MAR04-RUSSIA", "type": "Political", "open_price": 0.90, "resolved_yes": True, "pnl": 0.10},
]

df = pd.DataFrame(data)

# Apply filters
df = df[(df["open_price"] >= min_prob) & (df["open_price"] <= max_prob)]
if market_filter != "All":
    df = df[df["type"] == market_filter]

# Metrics row
col1, col2, col3, col4 = st.columns(4)
if len(df) > 0:
    win_rate = df["resolved_yes"].mean() * 100
    total_pnl = df["pnl"].sum()
    sharpe = df["pnl"].mean() / df["pnl"].std() if df["pnl"].std() > 0 else 0
    col1.metric("Total Trades", len(df))
    col2.metric("Win Rate", f"{win_rate:.1f}%")
    col3.metric("Total PnL", f"{total_pnl:.3f}")
    col4.metric("Sharpe Ratio", f"{sharpe:.2f}")
else:
    st.warning("No trades match your filters.")

st.markdown("---")

# Charts
if len(df) > 0:
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("PnL by Probability Bucket")
        df['prob_bucket'] = pd.cut(df['open_price'],
                                    bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
                                    labels=['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'])
        bucket_pnl = df.groupby("prob_bucket")["pnl"].sum()
        colors = ["#DC2626" if x < 0 else "#00C2A8" for x in bucket_pnl]
        fig, ax = plt.subplots()
        ax.bar(bucket_pnl.index, bucket_pnl.values, color=colors)
        ax.axhline(y=0, color="black", linewidth=0.8, linestyle="--")
        ax.set_xlabel("Opening Probability")
        ax.set_ylabel("PnL (units)")
        st.pyplot(fig)

    with col_right:
        st.subheader("Cumulative PnL")
        df_sorted = df.sort_values("open_price").reset_index(drop=True)
        df_sorted["cumulative_pnl"] = df_sorted["pnl"].cumsum()
        fig2, ax2 = plt.subplots()
        ax2.plot(df_sorted.index, df_sorted["cumulative_pnl"], color="#6C47FF", linewidth=2)
        ax2.fill_between(df_sorted.index, df_sorted["cumulative_pnl"], alpha=0.1, color="#6C47FF")
        ax2.axhline(y=0, color="black", linewidth=0.8, linestyle="--")
        ax2.set_xlabel("Trade #")
        ax2.set_ylabel("Cumulative PnL")
        st.pyplot(fig2)

    st.markdown("---")
    st.subheader("Trade Log")
    st.dataframe(df[["ticker", "type", "open_price", "resolved_yes", "pnl"]].reset_index(drop=True))


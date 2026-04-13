"""backtest_tab.py — Callibr strategy backtesting module.

Called from app.py via render_backtest_tab(). All Streamlit UI lives here;
app.py passes in shared helpers to avoid re-defining them.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import date, timedelta
from scipy.stats import norm as _scipy_norm

# ── design tokens (mirrors app.py) ────────────────────────────────────────────
_BG0   = "#080b0f"
_BG1   = "#0f1318"
_BG2   = "#14181e"
_BG3   = "#1c2028"
_BORD  = "#1e2530"
_T1    = "#eef2f9"
_T2    = "#999ea6"
_T3    = "#4a5060"
_RED   = "#f90000"
_GREEN = "#00C2A8"
_AMBER = "#F59E0B"
_BLUE  = "#3B82F6"
_PURP  = "#8B5CF6"

_PLOT_BASE = dict(
    paper_bgcolor=_BG1, plot_bgcolor=_BG1,
    font=dict(family="'Geist Mono','Courier New',monospace", color=_T3, size=10),
    margin=dict(l=16, r=16, t=40, b=16),
    xaxis=dict(gridcolor=_BORD, linecolor=_BORD, tickfont=dict(size=9)),
    yaxis=dict(gridcolor=_BORD, linecolor=_BORD, tickfont=dict(size=9)),
    hoverlabel=dict(
        bgcolor=_BG2, bordercolor=_BORD,
        font=dict(family="'Geist Mono','Courier New',monospace", size=11, color=_T1),
    ),
)

# ── safe builtins for user strategy sandbox ────────────────────────────────────
_SAFE_BUILTINS = {
    "abs": abs, "max": max, "min": min, "len": len,
    "round": round, "int": int, "float": float, "str": str,
    "bool": bool, "list": list, "dict": dict, "range": range,
    "True": True, "False": False, "None": None,
}
_BLOCKED_PATTERNS = [
    "import os", "import sys", "import subprocess", "import socket",
    "import shutil", "open(", "__import__", "exec(", "eval(",
    "compile(", "__builtins__",
]

# ── default strategy template ──────────────────────────────────────────────────
_DEFAULT_STRATEGY = """\
def signal(row) -> bool:
    \"\"\"Return True to enter a YES trade on this market.

    Available columns:
      open_price       float  — first observed price (your entry)
      final_price      float  — last observed price
      edge_score       int    — 0-100 (higher = more edge)
      price_change_pct float  — % move from open to final
      snapshot_count   int    — liquidity proxy (more = better)
      price_std        float  — price volatility
      days_to_close    int    — urgency
      category         str    — e.g. "Sports", "Politics & Macro"
      source           str    — "polymarket" or "kalshi"
      resolved         str    — "YES" or "NO"
    \"\"\"
    return row['edge_score'] > 40 and row['open_price'] < 0.5
"""


# ──────────────────────────────────────────────────────────────────────────────
# Data loading
# ──────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def _load_csv(csv_path: str, date_from: str, date_to: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, low_memory=False)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"])
    mask = (
        (df["timestamp"] >= pd.Timestamp(date_from, tz="UTC")) &
        (df["timestamp"] <= pd.Timestamp(date_to, tz="UTC") + pd.Timedelta(days=1))
    )
    return df[mask].copy()


def _load_supabase(supabase_client, date_from: str, date_to: str) -> pd.DataFrame:
    rows = []
    cursor = None
    date_from_iso = pd.Timestamp(date_from, tz="UTC").isoformat()
    date_to_iso   = (pd.Timestamp(date_to, tz="UTC") + pd.Timedelta(days=1)).isoformat()
    for _ in range(200):
        q = (
            supabase_client.table("market_prices")
            .select("timestamp,source,ticker,event_ticker,mid_price,open_time,close_time")
            .gte("timestamp", date_from_iso)
            .lte("timestamp", date_to_iso)
            .limit(1000)
        )
        if cursor:
            q = q.gt("id", cursor)
        res = q.execute()
        batch = res.data or []
        rows.extend(batch)
        if len(batch) < 1000:
            break
        cursor = batch[-1].get("id")
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    return df


def load_backtest_data(
    source: str,
    date_from: str,
    date_to: str,
    supabase_client=None,
    csv_path: str = "market_prices.csv",
) -> pd.DataFrame:
    if source == "CSV":
        return _load_csv(csv_path, date_from, date_to)
    return _load_supabase(supabase_client, date_from, date_to)


# ──────────────────────────────────────────────────────────────────────────────
# Universe builder
# ──────────────────────────────────────────────────────────────────────────────

def build_backtest_universe(
    df_raw: pd.DataFrame,
    categorize_fn,
    compute_edge_fn,
    resolution_threshold: float = 0.90,
) -> pd.DataFrame:
    df = df_raw.copy()
    df["mid_price"] = pd.to_numeric(df["mid_price"], errors="coerce")
    df = df.dropna(subset=["mid_price", "ticker"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"])

    df_sorted = df.sort_values("timestamp")

    first = df_sorted.groupby("ticker").first().reset_index()
    last  = df_sorted.groupby("ticker").last().reset_index()
    snaps = df_sorted.groupby("ticker").size().reset_index(name="snapshot_count")
    stds  = df_sorted.groupby("ticker")["mid_price"].std().reset_index(name="price_std")

    m = first.rename(columns={"mid_price": "open_price", "timestamp": "first_seen"})
    m = m.merge(
        last[["ticker", "mid_price", "timestamp"]].rename(
            columns={"mid_price": "final_price", "timestamp": "last_seen"}
        ),
        on="ticker", how="left"
    )
    m = m.merge(snaps, on="ticker", how="left")
    m = m.merge(stds,  on="ticker", how="left")
    m["price_std"]      = m["price_std"].fillna(0)
    m["snapshot_count"] = m["snapshot_count"].fillna(1).astype(int)
    m["category"]       = m["event_ticker"].fillna("").apply(categorize_fn)
    m["price_change_pct"] = (
        (m["final_price"] - m["open_price"]) /
        m["open_price"].clip(lower=0.01) * 100
    ).clip(-200, 200).round(2)
    m["close_time"]     = pd.to_datetime(m["close_time"], errors="coerce", utc=True)
    m["days_to_close"]  = (
        (m["close_time"] - m["first_seen"]).dt.total_seconds() / 86400
    ).fillna(30).clip(lower=0).round(0).astype(int)

    lo = 1.0 - resolution_threshold
    m["resolved"] = m["final_price"].apply(
        lambda p: "YES" if p >= resolution_threshold
                  else ("NO" if p <= lo else "UNRESOLVED")
    )
    total = len(m)
    m = m[m["resolved"] != "UNRESOLVED"].copy()
    m["resolved_yes"] = (m["resolved"] == "YES").astype(int)
    m["current_price"] = m["open_price"]
    cat_avg = m.groupby("category")["price_change_pct"].mean().to_dict()
    m["edge_score"] = m.apply(lambda r: compute_edge_fn(r, cat_avg), axis=1)
    m["_total_markets"] = total
    return m.reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────────
# Strategy execution
# ──────────────────────────────────────────────────────────────────────────────

def apply_preset_strategy(
    df: pd.DataFrame,
    min_edge: int,
    min_price: float,
    max_price: float,
    source_filter: str,
    category_filter: str,
) -> pd.DataFrame:
    mask = (
        (df["edge_score"] >= min_edge) &
        (df["open_price"] >= min_price) &
        (df["open_price"] <= max_price)
    )
    if source_filter != "All":
        mask &= df["source"].str.lower() == source_filter.lower()
    if category_filter != "All":
        mask &= df["category"] == category_filter
    return df[mask].copy()


def run_custom_strategy(df: pd.DataFrame, code: str) -> tuple[pd.DataFrame, str]:
    code = code.strip()
    for pat in _BLOCKED_PATTERNS:
        if pat in code:
            return df.iloc[0:0], f"Blocked pattern: `{pat}`"
    ns: dict = {}
    try:
        exec(compile(code, "<strategy>", "exec"), {"__builtins__": _SAFE_BUILTINS}, ns)
    except SyntaxError as e:
        return df.iloc[0:0], f"Syntax error: {e}"
    signal_fn = ns.get("signal")
    if not callable(signal_fn):
        return df.iloc[0:0], "Strategy must define a function named `signal(row)`."
    fired = []
    for _, row in df.iterrows():
        try:
            result = bool(signal_fn(row.to_dict()))
        except Exception:
            result = False
        fired.append(result)
    return df[fired].copy(), ""


# ──────────────────────────────────────────────────────────────────────────────
# PnL simulation
# ──────────────────────────────────────────────────────────────────────────────

def simulate_pnl(
    df_trades: pd.DataFrame,
    stake: float = 1.0,
    slippage: float = 0.01,
) -> pd.DataFrame:
    df = df_trades.copy()
    df["effective_entry"] = (df["open_price"] + slippage).clip(upper=0.99)
    df["pnl"] = df.apply(
        lambda r: (1.0 - r["effective_entry"]) * stake
                  if r["resolved_yes"] == 1
                  else (-r["effective_entry"]) * stake,
        axis=1,
    )
    df["roi_pct"] = df.apply(
        lambda r: (1.0 - r["effective_entry"]) / r["effective_entry"] * 100
                  if r["resolved_yes"] == 1
                  else -100.0,
        axis=1,
    )
    df["prob_bucket"] = pd.cut(
        df["open_price"],
        bins=[0, 0.2, 0.4, 0.6, 0.8, 1.0],
        labels=["0–20%", "20–40%", "40–60%", "60–80%", "80–100%"],
    )
    df = df.sort_values("first_seen").reset_index(drop=True)
    df["cumulative_pnl"] = df["pnl"].cumsum()
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Statistics (QuantConnect-style tearsheet metrics)
# ──────────────────────────────────────────────────────────────────────────────

def compute_stats(df: pd.DataFrame, stake: float = 1.0) -> dict:
    r = df["pnl"]
    n = len(r)
    wins  = df[df["resolved_yes"] == 1]
    losses = df[df["resolved_yes"] == 0]

    # Returns
    total_pnl    = r.sum()
    total_return = total_pnl / (n * stake) * 100 if n > 0 else 0.0

    # Risk-adjusted
    std = r.std()
    sharpe  = r.mean() / std * np.sqrt(252) if std > 0 else 0.0

    downside_r = r[r < 0]
    sortino_denom = downside_r.std() if len(downside_r) > 1 else 1e-9
    sortino = r.mean() / sortino_denom * np.sqrt(252)

    # Drawdown
    cumulative = df["cumulative_pnl"]
    running_max = cumulative.cummax()
    drawdown    = cumulative - running_max
    max_dd      = drawdown.min()

    # Max drawdown duration (in trades)
    in_dd = drawdown < 0
    dd_dur = 0
    cur_dur = 0
    for v in in_dd:
        if v:
            cur_dur += 1
            dd_dur = max(dd_dur, cur_dur)
        else:
            cur_dur = 0

    calmar = (total_pnl / abs(max_dd)) if max_dd < 0 else float("inf")
    recovery_factor = (total_pnl / abs(max_dd)) if max_dd < 0 else float("inf")

    # Win/loss
    win_rate  = len(wins) / n if n > 0 else 0.0
    avg_win   = wins["pnl"].mean()   if len(wins)   > 0 else 0.0
    avg_loss  = losses["pnl"].mean() if len(losses) > 0 else 0.0
    profit_factor = (
        wins["pnl"].sum() / abs(losses["pnl"].sum())
        if len(losses) > 0 and losses["pnl"].sum() != 0 else float("inf")
    )
    payoff_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float("inf")

    # Expected value
    ev = win_rate * avg_win + (1 - win_rate) * avg_loss

    # Kelly criterion
    if avg_loss != 0 and payoff_ratio != float("inf"):
        kelly = win_rate - (1 - win_rate) / payoff_ratio
    else:
        kelly = 0.0

    # Streaks
    outcomes = df["resolved_yes"].tolist()
    max_win_streak = max_loss_streak = cur_w = cur_l = 0
    for o in outcomes:
        if o == 1:
            cur_w += 1; cur_l = 0
            max_win_streak = max(max_win_streak, cur_w)
        else:
            cur_l += 1; cur_w = 0
            max_loss_streak = max(max_loss_streak, cur_l)

    # Probabilistic Sharpe (simplified)
    psr = float("nan")
    if n > 1 and std > 0:
        sr_hat = r.mean() / std
        skew   = float(pd.Series(r).skew())
        kurt   = float(pd.Series(r).kurtosis())
        sr_se  = np.sqrt((1 + (0.5 * sr_hat**2) - skew * sr_hat + ((kurt - 3) / 4) * sr_hat**2) / (n - 1))
        psr    = float(_scipy_norm.cdf(sr_hat / sr_se)) if sr_se > 0 else float("nan")

    return {
        "n_trades":          n,
        "win_rate":          win_rate,
        "total_pnl":         total_pnl,
        "total_return_pct":  total_return,
        "avg_pnl":           r.mean(),
        "avg_win":           avg_win,
        "avg_loss":          avg_loss,
        "best_trade":        r.max(),
        "worst_trade":       r.min(),
        "profit_factor":     profit_factor,
        "payoff_ratio":      payoff_ratio,
        "expected_value":    ev,
        "kelly":             kelly,
        "sharpe":            sharpe,
        "sortino":           sortino,
        "calmar":            calmar,
        "recovery_factor":   recovery_factor,
        "max_drawdown":      max_dd,
        "max_dd_duration":   dd_dur,
        "max_win_streak":    max_win_streak,
        "max_loss_streak":   max_loss_streak,
        "avg_roi_pct":       df["roi_pct"].mean(),
        "psr":               psr,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Charts
# ──────────────────────────────────────────────────────────────────────────────

def _lay(fig, title="", height=280, **extra):
    kw = {**_PLOT_BASE, "title": dict(text=title, font=dict(size=11, color=_T2)), "height": height}
    kw.update(extra)
    fig.update_layout(**kw)
    return fig


def _chart_equity_drawdown(df: pd.DataFrame) -> go.Figure:
    """Stacked equity curve + underwater drawdown chart (QuantConnect signature)."""
    cumulative = df["cumulative_pnl"]
    running_max = cumulative.cummax()
    drawdown    = cumulative - running_max
    dd_pct      = (drawdown / running_max.replace(0, np.nan)).fillna(0) * 100
    x = df.index

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.65, 0.35], vertical_spacing=0.04,
    )
    color = _GREEN if cumulative.iloc[-1] >= 0 else _RED
    fill  = "rgba(0,194,168,0.08)" if color == _GREEN else "rgba(249,0,0,0.08)"

    # Equity
    fig.add_trace(go.Scatter(
        x=x, y=cumulative, mode="lines", name="Equity",
        line=dict(color=color, width=2), fill="tozeroy", fillcolor=fill,
        hovertemplate="Trade #%{x}<br>PnL: %{y:.3f}<extra></extra>",
    ), row=1, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color=_BORD, row=1, col=1)

    # Drawdown
    fig.add_trace(go.Scatter(
        x=x, y=dd_pct, mode="lines", name="Drawdown %",
        line=dict(color=_RED, width=1.5), fill="tozeroy",
        fillcolor="rgba(249,0,0,0.12)",
        hovertemplate="Trade #%{x}<br>Drawdown: %{y:.1f}%<extra></extra>",
    ), row=2, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color=_BORD, row=2, col=1)

    fig.update_layout(
        **_PLOT_BASE,
        height=380, showlegend=False,
        title=dict(text="Equity Curve & Drawdown", font=dict(size=11, color=_T2)),
        yaxis=dict(gridcolor=_BORD, linecolor=_BORD, tickfont=dict(size=9), title="PnL"),
        yaxis2=dict(gridcolor=_BORD, linecolor=_BORD, tickfont=dict(size=9), title="DD %"),
        xaxis2=dict(gridcolor=_BORD, linecolor=_BORD, tickfont=dict(size=9), title="Trade #"),
    )
    return fig


def _chart_monthly_heatmap(df: pd.DataFrame) -> go.Figure:
    """Monthly returns heatmap (rows = years, cols = months)."""
    d = df.copy()
    d["month"] = d["first_seen"].dt.month
    d["year"]  = d["first_seen"].dt.year

    monthly = d.groupby(["year", "month"])["pnl"].sum().reset_index()
    years  = sorted(monthly["year"].unique())
    months = list(range(1, 13))
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    z = []
    text = []
    for yr in years:
        row_z = []
        row_t = []
        yr_data = monthly[monthly["year"] == yr]
        for mo in months:
            val = yr_data[yr_data["month"] == mo]["pnl"]
            v = float(val.values[0]) if len(val) else float("nan")
            row_z.append(v)
            row_t.append(f"{v:+.2f}" if not np.isnan(v) else "")
        z.append(row_z)
        text.append(row_t)

    if not years:
        fig = go.Figure()
        return _lay(fig, "Monthly Returns", height=160)

    fig = go.Figure(go.Heatmap(
        x=month_names, y=[str(y) for y in years], z=z,
        text=text, texttemplate="%{text}",
        colorscale=[[0, _RED], [0.5, _BG3], [1, _GREEN]],
        zmid=0, showscale=True,
        hoverongaps=False,
        hovertemplate="<b>%{y} %{x}</b><br>PnL: %{z:.3f}<extra></extra>",
        colorbar=dict(
            thickness=8, len=0.8,
            tickfont=dict(size=8, color=_T3),
            outlinewidth=0,
        ),
        xgap=2, ygap=2,
    ))
    h = max(160, len(years) * 44 + 60)
    fig.update_layout(
        **_PLOT_BASE, height=h,
        title=dict(text="Monthly Returns (PnL)", font=dict(size=11, color=_T2)),
        xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=9)),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=9)),
    )
    return fig


def _chart_rolling_sharpe(df: pd.DataFrame, window: int = 20) -> go.Figure:
    r = df["pnl"]
    roll_sharpe = (
        r.rolling(window).mean() / r.rolling(window).std() * np.sqrt(252)
    ).fillna(0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=roll_sharpe, mode="lines", name=f"Sharpe ({window}-trade)",
        line=dict(color=_PURP, width=1.5),
        hovertemplate="Trade #%{x}<br>Rolling Sharpe: %{y:.2f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color=_BORD)
    fig.add_hline(y=1, line_dash="dash", line_color=_AMBER,
                  annotation_text="Sharpe = 1", annotation_font_color=_AMBER,
                  annotation_position="top right")
    return _lay(fig, f"Rolling Sharpe ({window}-trade window)", height=220)


def _chart_rolling_winrate(df: pd.DataFrame, window: int = 20) -> go.Figure:
    wr = df["resolved_yes"].rolling(window).mean() * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=wr, mode="lines", name="Win Rate",
        line=dict(color=_GREEN, width=1.5), fill="tozeroy",
        fillcolor="rgba(0,194,168,0.07)",
        hovertemplate="Trade #%{x}<br>Win Rate: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=50, line_dash="dash", line_color=_AMBER,
                  annotation_text="50%", annotation_font_color=_AMBER,
                  annotation_position="top right")
    return _lay(fig, f"Rolling Win Rate ({window}-trade window)", height=220)


def _chart_return_dist(df: pd.DataFrame) -> go.Figure:
    """Return distribution with normal overlay."""
    r = df["pnl"]
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=r, nbinsx=30, name="Returns",
        marker_color=_BLUE, opacity=0.75,
        hovertemplate="PnL: %{x:.3f}<br>Count: %{y}<extra></extra>",
    ))
    # Normal overlay
    mu, sigma = r.mean(), r.std()
    if sigma > 0:
        x_norm = np.linspace(r.min(), r.max(), 200)
        y_norm = (
            np.exp(-0.5 * ((x_norm - mu) / sigma) ** 2)
            / (sigma * np.sqrt(2 * np.pi))
        ) * len(r) * (r.max() - r.min()) / 30
        fig.add_trace(go.Scatter(
            x=x_norm, y=y_norm, mode="lines", name="Normal",
            line=dict(color=_AMBER, width=1.5, dash="dash"),
        ))
    fig.add_vline(x=0, line_dash="dot", line_color=_BORD)
    fig.add_vline(x=mu, line_color=_GREEN, line_width=1,
                  annotation_text=f"μ={mu:+.3f}", annotation_font_color=_GREEN,
                  annotation_position="top left")
    return _lay(fig, "Return Distribution", height=240,
                showlegend=True,
                legend=dict(font=dict(size=9, color=_T3), bgcolor="rgba(0,0,0,0)"))


def _chart_calibration(df: pd.DataFrame) -> go.Figure:
    """Implied probability vs actual win rate — key for prediction markets."""
    d = df.copy()
    d["price_bin"] = pd.cut(
        d["open_price"],
        bins=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        labels=[0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95],
    )
    cal = d.groupby("price_bin", observed=True).agg(
        actual_wr=("resolved_yes", "mean"),
        n=("resolved_yes", "count"),
    ).reset_index()
    cal["price_bin"] = cal["price_bin"].astype(float)
    cal = cal[cal["n"] >= 2]

    fig = go.Figure()
    # Perfect calibration line
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode="lines", name="Perfect calibration",
        line=dict(color=_T3, width=1, dash="dash"),
    ))
    # Actual calibration
    fig.add_trace(go.Scatter(
        x=cal["price_bin"], y=cal["actual_wr"],
        mode="markers+lines", name="Actual",
        marker=dict(color=_GREEN, size=cal["n"].clip(upper=20) / 2 + 4,
                    line=dict(color=_BORD, width=1)),
        line=dict(color=_GREEN, width=1.5),
        hovertemplate="Implied: %{x:.0%}<br>Actual: %{y:.1%}<br>n=%{customdata}",
        customdata=cal["n"],
    ))
    fig.update_xaxes(tickformat=".0%", range=[-0.05, 1.05])
    fig.update_yaxes(tickformat=".0%", range=[-0.05, 1.05])
    return _lay(fig, "Market Calibration (Implied vs Actual Win Rate)", height=280,
                showlegend=True,
                legend=dict(font=dict(size=9, color=_T3), bgcolor="rgba(0,0,0,0)"))


def _chart_bucket_pnl(df: pd.DataFrame) -> go.Figure:
    bp = df.groupby("prob_bucket", observed=True)["pnl"].sum().reset_index()
    fig = go.Figure(go.Bar(
        x=bp["prob_bucket"].astype(str), y=bp["pnl"],
        marker_color=[_GREEN if v >= 0 else _RED for v in bp["pnl"]],
        hovertemplate="%{x}<br>PnL: %{y:.3f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color=_BORD)
    return _lay(fig, "PnL by Entry Price Bucket", height=220)


def _chart_category(df: pd.DataFrame) -> go.Figure:
    cat = (
        df.groupby("category")
        .agg(trades=("pnl", "count"), pnl=("pnl", "sum"))
        .reset_index().sort_values("pnl", ascending=True)
    )
    fig = go.Figure(go.Bar(
        x=cat["pnl"], y=cat["category"], orientation="h",
        marker_color=[_GREEN if v >= 0 else _RED for v in cat["pnl"]],
        hovertemplate="%{y}<br>PnL: %{x:.3f}<extra></extra>",
    ))
    fig.add_vline(x=0, line_dash="dot", line_color=_BORD)
    return _lay(fig, "PnL by Category", height=max(200, len(cat) * 30 + 60))


def _chart_win_loss_dist(df: pd.DataFrame) -> go.Figure:
    """Avg win vs avg loss bar comparison."""
    wins   = df[df["resolved_yes"] == 1]["pnl"]
    losses = df[df["resolved_yes"] == 0]["pnl"]
    labels = ["Avg Win", "Avg Loss", "Expected Value"]
    values = [
        wins.mean()   if len(wins)   > 0 else 0,
        losses.mean() if len(losses) > 0 else 0,
        df["pnl"].mean(),
    ]
    colors = [_GREEN, _RED, _AMBER]
    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=colors,
        hovertemplate="%{x}: %{y:.4f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color=_BORD)
    return _lay(fig, "Win / Loss Profile", height=220)


# ──────────────────────────────────────────────────────────────────────────────
# Tearsheet stats table (HTML)
# ──────────────────────────────────────────────────────────────────────────────

def _fmt(v, fmt=".3f", suffix=""):
    if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
        return "—"
    if fmt == "pct":
        return f"{v:.1%}"
    if fmt == "x":
        return f"{v:.2f}×"
    return f"{v:{fmt}}{suffix}"


def _stats_table_html(s: dict) -> str:
    pnl_color = _GREEN if s["total_pnl"] >= 0 else _RED

    def row(label, value, color=_T1):
        return f"""
<tr>
  <td style="color:{_T3};font-size:10px;padding:5px 12px 5px 0;
             border-bottom:1px solid {_BORD};white-space:nowrap;">{label}</td>
  <td style="color:{color};font-size:11px;font-weight:600;padding:5px 0;
             border-bottom:1px solid {_BORD};text-align:right;">{value}</td>
</tr>"""

    left_rows = [
        row("Total Trades",       _fmt(s["n_trades"],        "d")),
        row("Win Rate",           _fmt(s["win_rate"],        "pct"), _GREEN if s["win_rate"] >= 0.5 else _RED),
        row("Total PnL",          _fmt(s["total_pnl"],       "+.3f"), pnl_color),
        row("Total Return",       _fmt(s["total_return_pct"],"+.1f", "%"), pnl_color),
        row("Avg Trade PnL",      _fmt(s["avg_pnl"],         "+.4f"), _GREEN if s["avg_pnl"] >= 0 else _RED),
        row("Avg Win",            _fmt(s["avg_win"],         "+.4f"), _GREEN),
        row("Avg Loss",           _fmt(s["avg_loss"],        "+.4f"), _RED),
        row("Best Trade",         _fmt(s["best_trade"],      "+.4f"), _GREEN),
        row("Worst Trade",        _fmt(s["worst_trade"],     "+.4f"), _RED),
        row("Profit Factor",      _fmt(s["profit_factor"],   ".2f"),  _GREEN if s["profit_factor"] > 1 else _RED),
        row("Payoff Ratio",       _fmt(s["payoff_ratio"],    ".2f")),
        row("Expected Value",     _fmt(s["expected_value"],  "+.4f"), _GREEN if s["expected_value"] >= 0 else _RED),
    ]
    sharpe_c = _GREEN if s["sharpe"] >= 1 else (_AMBER if s["sharpe"] >= 0 else _RED)
    right_rows = [
        row("Sharpe Ratio",       _fmt(s["sharpe"],           ".3f"), sharpe_c),
        row("Sortino Ratio",      _fmt(s["sortino"],          ".3f"), _GREEN if s["sortino"] >= 1 else _AMBER),
        row("Calmar Ratio",       _fmt(s["calmar"],           ".3f")),
        row("Max Drawdown",       _fmt(s["max_drawdown"],     "+.3f"), _RED),
        row("Max DD Duration",    f"{s['max_dd_duration']} trades"),
        row("Recovery Factor",    _fmt(s["recovery_factor"],  ".2f")),
        row("Kelly Criterion",    _fmt(s["kelly"],            ".1%"),  _GREEN if s["kelly"] > 0 else _RED),
        row("Prob. Sharpe Ratio", _fmt(s["psr"],              ".1%") if not np.isnan(s["psr"]) else "—"),
        row("Avg ROI / Trade",    _fmt(s["avg_roi_pct"],      "+.1f", "%")),
        row("Win Streak",         f"{s['max_win_streak']} trades",     _GREEN),
        row("Loss Streak",        f"{s['max_loss_streak']} trades",    _RED),
        row("",                   ""),
    ]

    left_html  = "".join(left_rows)
    right_html = "".join(right_rows)

    return f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:0 32px;
            background:{_BG2};border:1px solid {_BORD};border-radius:2px;
            padding:16px 20px;margin-bottom:24px;">
  <div>
    <div style="font-size:9px;letter-spacing:0.18em;color:{_T3};
                text-transform:uppercase;font-weight:600;
                padding-bottom:8px;border-bottom:1px solid {_BORD};
                margin-bottom:4px;">Performance</div>
    <table style="width:100%;border-collapse:collapse;">{left_html}</table>
  </div>
  <div>
    <div style="font-size:9px;letter-spacing:0.18em;color:{_T3};
                text-transform:uppercase;font-weight:600;
                padding-bottom:8px;border-bottom:1px solid {_BORD};
                margin-bottom:4px;">Risk</div>
    <table style="width:100%;border-collapse:collapse;">{right_html}</table>
  </div>
</div>
"""


# ──────────────────────────────────────────────────────────────────────────────
# Main render function (called from app.py)
# ──────────────────────────────────────────────────────────────────────────────

def render_backtest_tab(supabase_client, categorize_fn, compute_edge_fn):
    st.markdown(f"""
<style>
.bt-header {{
  font-size:10px; letter-spacing:0.18em; color:{_T3};
  text-transform:uppercase; font-weight:600;
  margin-bottom:10px; padding-bottom:6px;
  border-bottom:1px solid {_BORD};
}}
</style>
""", unsafe_allow_html=True)

    left, right = st.columns([1, 2], gap="large")

    # ── LEFT PANEL ─────────────────────────────────────────────────────────────
    with left:
        st.markdown('<div class="bt-header">Data Source</div>', unsafe_allow_html=True)
        data_source = st.radio(
            "Source", ["CSV", "Supabase"],
            horizontal=True, label_visibility="collapsed", key="bt_data_source",
        )

        st.markdown('<div class="bt-header" style="margin-top:18px;">Date Range</div>', unsafe_allow_html=True)
        d1, d2 = st.columns(2)
        with d1:
            date_from = st.date_input("From", value=date.today() - timedelta(days=30),
                                      key="bt_date_from", label_visibility="collapsed")
        with d2:
            date_to = st.date_input("To", value=date.today(),
                                    key="bt_date_to", label_visibility="collapsed")
        st.caption(f"{date_from}  →  {date_to}")

        st.markdown('<div class="bt-header" style="margin-top:18px;">Resolution Threshold</div>', unsafe_allow_html=True)
        res_threshold = st.slider(
            "Threshold", 0.80, 0.99, 0.90, 0.01,
            label_visibility="collapsed", key="bt_res_thresh",
            help="final_price ≥ threshold → YES, ≤ (1−threshold) → NO. Others excluded.",
        )

        st.markdown('<div class="bt-header" style="margin-top:18px;">Strategy</div>', unsafe_allow_html=True)
        strategy_mode = st.radio(
            "Mode", ["Preset rules", "Custom Python"],
            label_visibility="collapsed", key="bt_strat_mode",
        )

        if strategy_mode == "Preset rules":
            min_edge      = st.slider("Min edge score",   0, 100, 40, 5, key="bt_min_edge")
            price_range   = st.slider("Entry price range", 0.0, 1.0, (0.15, 0.85), 0.05, key="bt_price_range")
            source_filter = st.selectbox("Source filter",
                ["All", "polymarket", "kalshi"], key="bt_src_filter")
            cat_filter    = st.selectbox("Category filter",
                ["All", "Sports", "Politics & Macro", "Crypto",
                 "Tech & Markets", "Entertainment & Legal", "Other"],
                key="bt_cat_filter")
        else:
            user_code = st.text_area(
                "Code", value=_DEFAULT_STRATEGY, height=260,
                key="bt_code", label_visibility="collapsed",
            )

        st.markdown('<div class="bt-header" style="margin-top:18px;">Simulation</div>', unsafe_allow_html=True)
        s1, s2 = st.columns(2)
        with s1:
            stake    = st.number_input("Stake", value=1.0, min_value=0.01, step=0.5,
                                       key="bt_stake", label_visibility="collapsed")
            st.caption("Stake / trade")
        with s2:
            slippage = st.number_input("Slippage", value=0.01, min_value=0.0,
                                       max_value=0.10, step=0.005, format="%.3f",
                                       key="bt_slippage", label_visibility="collapsed")
            st.caption("Slippage")

        run = st.button("▶ Run Backtest", use_container_width=True,
                        type="primary", key="bt_run")

    # ── RIGHT PANEL ────────────────────────────────────────────────────────────
    with right:
        if not run and "bt_results" not in st.session_state:
            st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:center;
            height:340px;color:{_T3};font-size:11px;letter-spacing:0.1em;
            text-transform:uppercase;border:1px solid {_BORD};border-radius:2px;">
  Configure a strategy and click Run Backtest
</div>
""", unsafe_allow_html=True)

        if run:
            with st.spinner("Loading market data..."):
                try:
                    raw = load_backtest_data(
                        source=data_source,
                        date_from=str(date_from),
                        date_to=str(date_to),
                        supabase_client=supabase_client,
                    )
                except Exception as e:
                    st.error(f"Data load failed: {e}")
                    st.stop()

            if raw.empty:
                st.warning("No data found for the selected date range.")
                st.stop()

            with st.spinner("Building market universe..."):
                universe = build_backtest_universe(
                    raw, categorize_fn, compute_edge_fn, res_threshold,
                )

            total_raw      = int(universe["_total_markets"].iloc[0]) if not universe.empty else 0
            total_resolved = len(universe)

            if universe.empty:
                st.warning(f"No resolved markets in this date range (threshold {res_threshold:.0%}).")
                st.stop()

            with st.spinner("Running strategy..."):
                if strategy_mode == "Preset rules":
                    trades = apply_preset_strategy(
                        universe,
                        min_edge=min_edge,
                        min_price=price_range[0],
                        max_price=price_range[1],
                        source_filter=source_filter,
                        category_filter=cat_filter,
                    )
                    err = ""
                else:
                    trades, err = run_custom_strategy(universe, user_code)

            if err:
                st.error(f"Strategy error: {err}")
                st.stop()

            if trades.empty:
                st.info(f"Strategy fired 0 trades out of {total_resolved} resolved markets.")
                st.stop()

            df_pnl = simulate_pnl(trades, stake=stake, slippage=slippage)
            st.session_state["bt_results"] = df_pnl
            st.session_state["bt_meta"]    = (total_raw, total_resolved, stake)

        # ── Render tearsheet ──────────────────────────────────────────────────
        if "bt_results" in st.session_state:
            df_pnl = st.session_state["bt_results"]
            total_raw, total_resolved, _stake = st.session_state.get("bt_meta", (0, 0, 1.0))
            stats = compute_stats(df_pnl, stake=_stake)

            st.caption(
                f"Universe: **{total_raw}** markets total → "
                f"**{total_resolved}** resolved → "
                f"**{stats['n_trades']}** trades triggered"
            )

            # ── Stats table ───────────────────────────────────────────────
            st.markdown(_stats_table_html(stats), unsafe_allow_html=True)

            # ── Equity + Drawdown (stacked) ───────────────────────────────
            st.plotly_chart(_chart_equity_drawdown(df_pnl), use_container_width=True)

            # ── Monthly heatmap ───────────────────────────────────────────
            st.plotly_chart(_chart_monthly_heatmap(df_pnl), use_container_width=True)

            # ── Rolling metrics ───────────────────────────────────────────
            if len(df_pnl) >= 10:
                win = min(20, len(df_pnl) // 2)
                r1, r2 = st.columns(2)
                with r1:
                    st.plotly_chart(_chart_rolling_sharpe(df_pnl, win), use_container_width=True)
                with r2:
                    st.plotly_chart(_chart_rolling_winrate(df_pnl, win), use_container_width=True)

            # ── Distribution + Calibration ────────────────────────────────
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(_chart_return_dist(df_pnl), use_container_width=True)
            with c2:
                st.plotly_chart(_chart_calibration(df_pnl), use_container_width=True)

            # ── Bucket PnL + Win/Loss profile ─────────────────────────────
            c3, c4 = st.columns(2)
            with c3:
                st.plotly_chart(_chart_bucket_pnl(df_pnl), use_container_width=True)
            with c4:
                st.plotly_chart(_chart_win_loss_dist(df_pnl), use_container_width=True)

            # ── Category breakdown ────────────────────────────────────────
            st.plotly_chart(_chart_category(df_pnl), use_container_width=True)

            # ── Trade log ─────────────────────────────────────────────────
            st.markdown(
                f'<div class="bt-header" style="margin-top:4px;">Trade Log</div>',
                unsafe_allow_html=True,
            )
            disp = ["event_ticker", "source", "category",
                    "open_price", "effective_entry", "resolved",
                    "pnl", "roi_pct", "edge_score"]
            cols = [c for c in disp if c in df_pnl.columns]
            st.dataframe(
                df_pnl[cols].style.format({
                    "open_price":      "{:.3f}",
                    "effective_entry": "{:.3f}",
                    "pnl":             "{:+.3f}",
                    "roi_pct":         "{:+.1f}%",
                    "edge_score":      "{:.0f}",
                }),
                use_container_width=True, height=300,
            )
            st.download_button(
                "⬇ Download trade log",
                data=df_pnl[cols].to_csv(index=False),
                file_name="callibr_backtest.csv",
                mime="text/csv", key="bt_download",
            )

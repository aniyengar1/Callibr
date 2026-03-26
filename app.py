import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from supabase import create_client

st.set_page_config(page_title="Callibr", page_icon="🎯", layout="wide")

# ── design tokens (used in inline HTML throughout the file) ───────────────────
_BG0   = "#080b0f"   # deepest background
_BG1   = "#0f1318"   # page / app background
_BG2   = "#14181e"   # card surface
_BG3   = "#1c2028"   # elevated card / hover
_BORD  = "#1e2530"   # border
_T1    = "#eef2f9"   # primary text
_T2    = "#999ea6"   # secondary text
_T3    = "#4a5060"   # tertiary / placeholder
_RED   = "#f90000"   # accent red
_GREEN = "#00C2A8"   # positive edge / YES
_AMBER = "#F59E0B"   # warning / neutral
_BLUE  = "#3B82F6"   # kalshi
_PURP  = "#8B5CF6"   # polymarket

# ── custom CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@300;400;500;600;700&display=swap');

:root {{
  --bg0:    {_BG0};
  --bg1:    {_BG1};
  --bg2:    {_BG2};
  --bg3:    {_BG3};
  --bord:   {_BORD};
  --t1:     {_T1};
  --t2:     {_T2};
  --t3:     {_T3};
  --red:    {_RED};
  --green:  {_GREEN};
  --amber:  {_AMBER};
  --blue:   {_BLUE};
  --purp:   {_PURP};
  --font:   'Geist Mono', 'Courier New', monospace;
}}

/* ── global ── */
*, *::before, *::after {{ font-family: var(--font) !important; box-sizing: border-box; }}
html, body {{ background: var(--bg1) !important; color: var(--t1) !important; }}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
    background: var(--bg1) !important;
}}
p, li, span, div {{ color: var(--t1); }}

/* ── sidebar ── */
[data-testid="stSidebar"] {{
    background: var(--bg0) !important;
    border-right: 1px solid var(--bord) !important;
}}
[data-testid="stSidebar"] * {{ color: var(--t2) !important; }}

/* ── tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background: transparent;
    border-bottom: 1px solid var(--bord);
    gap: 0; padding: 0;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: var(--t3) !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 22px !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    transition: all 0.2s ease !important;
}}
.stTabs [data-baseweb="tab"]:hover {{ color: var(--t1) !important; }}
.stTabs [aria-selected="true"] {{
    color: var(--red) !important;
    border-bottom: 2px solid var(--red) !important;
    background: transparent !important;
}}
.stTabs [data-baseweb="tab-panel"] {{ padding-top: 28px; }}

/* ── metrics ── */
[data-testid="stMetric"] {{
    background: var(--bg2) !important;
    border: 1px solid var(--bord) !important;
    border-radius: 2px !important;
    padding: 16px 20px !important;
    transition: border-color 0.2s ease;
}}
[data-testid="stMetric"]:hover {{ border-color: var(--red) !important; }}
[data-testid="stMetricLabel"] {{
    color: var(--t3) !important;
    font-size: 9px !important;
    font-weight: 600 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
}}
[data-testid="stMetricValue"] {{
    color: var(--t1) !important;
    font-size: 22px !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em !important;
}}

/* ── headings ── */
h1, h2, h3, h4 {{
    color: var(--t1) !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}}
h2 {{ border-bottom: 1px solid var(--bord); padding-bottom: 10px; font-size: 14px !important; }}
h3 {{ font-size: 12px !important; color: var(--t2) !important; }}

/* ── buttons ── */
.stButton > button {{
    background: transparent !important;
    color: var(--t2) !important;
    border: 1px solid var(--bord) !important;
    border-radius: 1px !important;
    padding: 6px 14px !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    transition: all 0.18s ease !important;
}}
.stButton > button:hover {{
    border-color: var(--red) !important;
    color: var(--red) !important;
    transform: skew(-3deg) !important;
    background: rgba(249,0,0,0.05) !important;
}}
.stButton > button:active {{
    transform: skew(-3deg) scale(0.97) !important;
}}

/* ── inputs / selects ── */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {{
    background: var(--bg2) !important;
    border: 1px solid var(--bord) !important;
    border-radius: 1px !important;
    color: var(--t1) !important;
    font-size: 12px !important;
}}
.stSelectbox > div > div:focus-within,
.stTextInput > div > div > input:focus {{
    border-color: var(--red) !important;
    box-shadow: 0 0 0 1px var(--red) !important;
}}

/* ── sliders ── */
[data-testid="stSlider"] [role="slider"] {{ background: var(--red) !important; }}
[data-testid="stSlider"] [data-testid="stSliderThumb"] {{ background: var(--red) !important; }}

/* ── expanders ── */
[data-testid="stExpander"] {{
    background: var(--bg2) !important;
    border: 1px solid var(--bord) !important;
    border-radius: 2px !important;
    margin-bottom: 2px !important;
}}
[data-testid="stExpander"] summary {{
    color: var(--t1) !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    padding: 10px 14px !important;
}}
[data-testid="stExpander"] summary:hover {{ color: var(--red) !important; }}
[data-testid="stExpander"] details[open] summary {{
    border-bottom: 1px solid var(--bord) !important;
}}

/* ── dataframes ── */
[data-testid="stDataFrame"] {{
    border: 1px solid var(--bord) !important;
    border-radius: 2px !important;
    overflow: hidden;
}}
[data-testid="stDataFrame"] th {{
    background: var(--bg2) !important;
    color: var(--t3) !important;
    font-size: 9px !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid var(--bord) !important;
    font-weight: 600 !important;
}}
[data-testid="stDataFrame"] td {{
    color: var(--t2) !important;
    font-size: 11px !important;
    border-bottom: 1px solid rgba(30,37,48,0.6) !important;
}}
[data-testid="stDataFrame"] tr:hover td {{ background: rgba(249,0,0,0.03) !important; }}

/* ── alerts ── */
[data-testid="stAlert"], .stInfo, .stWarning, .stError {{
    background: var(--bg2) !important;
    border: 1px solid var(--bord) !important;
    border-radius: 1px !important;
    color: var(--t2) !important;
}}
.stInfo    {{ border-left: 2px solid var(--blue)  !important; }}
.stWarning {{ border-left: 2px solid var(--amber) !important; }}
.stError   {{ border-left: 2px solid var(--red)   !important; }}

/* ── caption / small text ── */
[data-testid="stCaptionContainer"], .stCaption {{
    color: var(--t3) !important;
    font-size: 10px !important;
    letter-spacing: 0.06em !important;
}}

/* ── hr ── */
hr {{ border: none; border-top: 1px solid var(--bord); margin: 24px 0; }}

/* ── tables (raw HTML) ── */
table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
table th {{
    background: var(--bg2); color: var(--t3);
    font-size: 9px; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    padding: 10px 14px; border-bottom: 1px solid var(--bord); text-align: left;
}}
table td {{ padding: 10px 14px; border-bottom: 1px solid rgba(30,37,48,0.5); color: var(--t2); }}
table tr:hover td {{ background: rgba(249,0,0,0.03); }}

/* ── plotly chart backgrounds ── */
.js-plotly-plot .plotly, .plot-container {{ background: transparent !important; }}
.modebar {{ background: transparent !important; }}

/* ── scrollbar ── */
::-webkit-scrollbar {{ width: 3px; height: 3px; }}
::-webkit-scrollbar-track {{ background: var(--bg0); }}
::-webkit-scrollbar-thumb {{ background: var(--bord); border-radius: 0; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--red); }}

/* ── scan-line overlay ── */
.main::after {{
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 3px,
        rgba(0,0,0,0.04) 3px,
        rgba(0,0,0,0.04) 4px
    );
    pointer-events: none;
    z-index: 9999;
}}

/* ── fix expander arrow (font override breaks Streamlit's icon font) ── */
.arrow_down, .arrow_up,
[class*="arrow_down"], [class*="arrow_up"],
p.arrow_down, p.arrow_up,
span.arrow_down, span.arrow_up,
div.arrow_down, div.arrow_up {{
    display: none !important;
}}
[data-testid="stExpander"] summary svg,
[data-testid="stExpander"] summary img {{
    display: none !important;
}}
[data-testid="stExpander"] summary::after {{
    content: '▾';
    font-size: 11px;
    color: var(--t3);
    margin-left: 6px;
    font-family: monospace !important;
    float: right;
}}
[data-testid="stExpander"] details[open] > summary::after {{
    content: '▴';
    color: var(--t2);
}}

/* ── hide Streamlit chrome ── */
#MainMenu, footer {{ visibility: hidden !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}
</style>
""", unsafe_allow_html=True)

# ── page header ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding:36px 0 24px 0; border-bottom:1px solid {_BORD}; margin-bottom:28px;">
    <div style="font-size:9px;font-weight:700;letter-spacing:0.22em;text-transform:uppercase;color:{_T3};margin-bottom:10px;">// PREDICTION MARKET INTELLIGENCE</div>
    <div style="font-size:36px;font-weight:700;color:{_T1};letter-spacing:0.06em;line-height:1;text-transform:uppercase;">CALLIBR</div>
    <div style="font-size:11px;color:{_T3};margin-top:10px;font-weight:400;letter-spacing:0.08em;text-transform:uppercase;">FIND MISPRICED MARKETS &nbsp;·&nbsp; RESEARCH ANY BET &nbsp;·&nbsp; GET YOUR EDGE</div>
</div>
""", unsafe_allow_html=True)

# ── constants ─────────────────────────────────────────────────────────────────
SUPABASE_URL      = st.secrets["SUPABASE_URL"]
SUPABASE_KEY      = st.secrets["SUPABASE_KEY"]
ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")
NEWSAPI_KEY       = st.secrets.get("NEWSAPI_KEY", "")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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

# Shared Plotly layout defaults
PLOT_LAYOUT = dict(
    paper_bgcolor=_BG1,
    plot_bgcolor=_BG1,
    font=dict(family="'Geist Mono', 'Courier New', monospace", color=_T3, size=10),
    margin=dict(l=16, r=16, t=36, b=16),
    xaxis=dict(gridcolor=_BORD, linecolor=_BORD, tickfont=dict(size=9)),
    yaxis=dict(gridcolor=_BORD, linecolor=_BORD, tickfont=dict(size=9)),
    hoverlabel=dict(
        bgcolor=_BG2,
        bordercolor=_BORD,
        font=dict(family="'Geist Mono', 'Courier New', monospace", size=11, color=_T1),
    ),
)

def apply_layout(fig, title="", height=300):
    fig.update_layout(**PLOT_LAYOUT, title=dict(text=title, font=dict(size=12, color="#666666")), height=height)
    return fig

# ── helpers ───────────────────────────────────────────────────────────────────
def categorize(question):
    q = question.lower()

    # ── Politics & Macro ──────────────────────────────────────────────────────
    if any(x in q for x in [
        "trump","biden","harris","obama","president","vice president",
        "election","midterm","primary","ballot","vote","voter","polling",
        "congress","senate","house of representatives","speaker","filibuster",
        "republican","democrat","gop","liberal","conservative","party",
        "ukraine","russia","putin","zelenskyy","nato","ceasefire","sanctions",
        "china","taiwan","xi jinping","hong kong","south china sea",
        "israel","gaza","hamas","iran","north korea","kim jong",
        "tariff","trade war","import","export","wto",
        "fed","federal reserve","jerome powell","interest rate","rate hike","rate cut",
        "inflation","cpi","pce","gdp","recession","unemployment","jobs report",
        "debt ceiling","budget","deficit","spending bill","government shutdown",
        "supreme court","scotus","justice","ruling","constitution",
        "eu","european union","g7","g20","imf","world bank",
        "prime minister","chancellor","parliament","brexit","macron","scholz",
        "poll","approval rating","swing state","electoral college",
        "executive order","veto","legislation","amendment","impeach",
    ]):
        return "Politics & Macro"

    # ── Sports ────────────────────────────────────────────────────────────────
    elif any(x in q for x in [
        "nba","nfl","mlb","nhl","mls","wnba","ufc","pga","lpga",
        "fifa","uefa","premier league","la liga","serie a","bundesliga","ligue 1",
        "champions league","europa league","world cup","euro","copa america",
        "ncaa","march madness","college football","cfp","bowl game",
        "formula 1","f1","nascar","indycar","motogp",
        "super bowl","stanley cup","world series","nba finals","nba championship",
        "wimbledon","us open","french open","australian open","masters","ryder cup",
        "olympics","medal","gold medal",
        "soccer","football","basketball","baseball","hockey","tennis","golf",
        "boxing","mma","wrestling","volleyball","rugby","cricket","cycling",
        "score","points","touchdown","homerun","home run","field goal","three pointer",
        "assist","rebound","strikeout","shutout","hat trick","overtime","playoff",
        "championship","tournament","season","draft","trade","roster","injury report",
        "mvp","all-star","hall of fame","win total","spread","over under","moneyline",
        "quarterback","pitcher","goalie","forward","midfielder","defender","center",
        "lebron","mahomes","messi","ronaldo","curry","jokic","luka","giannis",
        "sga","gilgeous","lamar jackson","burrow","judge","ohtani","shohei",
        "djokovic","federer","nadal","serena","tiger woods","mcilroy",
        "tatum","brown","jaylen","jayson","fox","bane","murray","morant","booker",
        "harden","durant","embiid","lillard","mitchell","doncic","jokić",
        "haaland","mbappe","salah","bellingham","vinicius","pedri","yamal",
        "alcaraz","sinner","swiatek","medvedev","zverev",
        "threes","rebounds","assists","steals","blocks","double double","triple double",
        "game 1","game 2","game 3","game 4","game 5","game 6","game 7",
        "first half","second half","first quarter","first period","regulation",
        "prop bet","player prop","team total","moneyline","ats","spread",
    ]):
        return "Sports"

    # ── Crypto ────────────────────────────────────────────────────────────────
    elif any(x in q for x in [
        "bitcoin","btc","ethereum","eth","solana","sol","cardano","ada",
        "xrp","ripple","dogecoin","doge","shiba","avax","avalanche",
        "polygon","matic","chainlink","link","uniswap","uni","aave",
        "bnb","binance","coinbase","kraken","ftx","celsius","blockfi",
        "crypto","cryptocurrency","blockchain","defi","nft","web3",
        "stablecoin","usdt","usdc","tether","dao","token","altcoin",
        "mining","proof of stake","proof of work","halving","satoshi",
        "metaverse","opensea","ledger","metamask","wallet","exchange",
        "sec crypto","crypto regulation","spot etf","bitcoin etf","crypto etf",
        "pump","dump","bull run","bear market","all time high","ath",
        "layer 2","rollup","zk proof","lightning network",
    ]):
        return "Crypto"

    # ── Tech & Markets ────────────────────────────────────────────────────────
    elif any(x in q for x in [
        "openai","chatgpt","gpt","anthropic","claude","gemini","llama","mistral",
        "google","alphabet","apple","microsoft","meta","amazon","netflix","tesla",
        "nvidia","amd","intel","qualcomm","arm","tsmc","samsung","asml",
        "uber","lyft","airbnb","doordash","instacart","stripe","plaid","klarna",
        "spacex","starlink","blue origin","boeing","lockheed",
        "stock","stocks","equity","share","ipo","spac","merger","acquisition",
        "earnings","revenue","profit","eps","guidance","valuation","market cap",
        "s&p","s&p 500","nasdaq","dow jones","russell","vix","spy","qqq",
        "hedge fund","private equity","venture capital","vc","angel investor",
        "bond","yield","treasury","10 year","2 year","yield curve","basis points",
        "oil","crude","wti","brent","opec","natural gas","energy prices",
        "gold","silver","commodities","futures","options","derivatives","forex",
        "artificial intelligence","machine learning","large language model","llm",
        "autonomous","self-driving","chip","semiconductor","data center","gpu",
        "cybersecurity","hack","breach","ransomware","data leak",
        "antitrust","ftc","doj","gdpr","sec","regulation tech",
        "layoffs","hiring","ceo","cto","founder","startup","unicorn",
    ]):
        return "Tech & Markets"

    # ── Entertainment & Legal ─────────────────────────────────────────────────
    elif any(x in q for x in [
        "album","song","single","tour","concert","grammy","billboard",
        "taylor swift","beyonce","rihanna","drake","kanye","ye","travis scott",
        "bad bunny","olivia rodrigo","billie eilish","ariana grande","the weeknd",
        "spotify","apple music","number one","platinum","chart","debut",
        "movie","film","box office","oscar","academy award","golden globe",
        "emmy","bafta","cannes","sundance","netflix show","hbo","disney plus","marvel",
        "dc comics","star wars","sequel","reboot","trailer","release date","premiere",
        "gta","video game","gaming","playstation","xbox","nintendo","steam","esports",
        "celebrity","kardashian","jenner","justin bieber","brad pitt","angelina",
        "divorce","marriage","engaged","baby","pregnant","feud","beef","drama",
        "trial","verdict","convicted","sentenced","acquitted","lawsuit","sued",
        "indicted","charged","arrested","plea","bail","prison","parole","appeal",
        "weinstein","epstein","defamation","case","jury","criminal","civil suit",
        "reality tv","bachelor","survivor","big brother","american idol",
    ]):
        return "Entertainment & Legal"

    # ── Other ─────────────────────────────────────────────────────────────────
    else:
        return "Other"

@st.cache_data(ttl=300)
def load_data():
    cutoff = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ts_cutoff = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    all_rows, offset, batch_size = [], 0, 1000
    while True:
        batch = supabase.table("market_prices").select("*")\
            .neq("source", "kalshi_historical")\
            .gte("close_time", cutoff)\
            .gte("timestamp", ts_cutoff)\
            .order("timestamp", desc=False)\
            .range(offset, offset + batch_size - 1).execute().data
        if not batch: break
        all_rows.extend(batch)
        if len(batch) < batch_size: break
        offset += batch_size
    if not all_rows: return pd.DataFrame()
    df = pd.DataFrame(all_rows)
    df["mid_price"] = pd.to_numeric(df["mid_price"], errors="coerce")
    df["category"]  = df["event_ticker"].apply(categorize)
    return df

def build_markets_df(df):
    df_first  = df.sort_values("timestamp").groupby("ticker").first().reset_index()
    df_latest = df.sort_values("timestamp").groupby("ticker").last().reset_index()
    df_latest = df_latest.rename(columns={"mid_price": "current_price"})
    df_m = df_first.merge(df_latest[["ticker","current_price"]], on="ticker")
    df_m["price_change"]     = (df_m["current_price"] - df_m["mid_price"]).round(4)
    df_m["price_change_pct"] = ((df_m["price_change"] / df_m["mid_price"]) * 100).round(2)
    # Cap outliers caused by near-zero opening prices
    df_m["price_change_pct"] = df_m["price_change_pct"].clip(-200, 200)
    df_m["days_to_close"]    = (
        pd.to_datetime(df_m["close_time"], errors="coerce").dt.tz_localize(None) - pd.Timestamp.now()
    ).dt.days
    # Liquidity proxy: count number of snapshots per ticker (more snapshots = more activity = more liquid)
    snapshot_counts = df.groupby("ticker").size().reset_index(name="snapshot_count")
    df_m = df_m.merge(snapshot_counts, on="ticker", how="left")
    df_m["snapshot_count"] = df_m["snapshot_count"].fillna(1)
    # Spread proxy: std of mid_price across snapshots (higher std = wider effective spread / more volatile)
    price_std = df.groupby("ticker")["mid_price"].std().reset_index(name="price_std")
    df_m = df_m.merge(price_std, on="ticker", how="left")
    df_m["price_std"] = df_m["price_std"].fillna(0)
    return df_m

def filter_skewed(df, min_price=0.01, max_price=0.99):
    """Remove effectively-resolved markets with no betting edge."""
    return df[(df["current_price"] > min_price) & (df["current_price"] < max_price)]

def parse_strategy_with_claude(user_input):
    system = """You are a trading strategy parser for a prediction markets backtesting platform.
Convert the user's plain-English strategy into structured rules.
Return ONLY a valid JSON object with exactly these fields:
{
  "condition": "less than" | "greater than" | "between",
  "threshold_1": <float 0.05-0.95>,
  "threshold_2": <float 0.05-0.95 or null>,
  "category": "All" | "Politics & Macro" | "Sports" | "Crypto" | "Tech & Markets" | "Entertainment & Legal" | "Other",
  "source": "all" | "polymarket" | "kalshi",
  "explanation": "<one sentence plain English summary of the rule>",
  "keywords": ["<3-6 short keywords or phrases extracted from the user intent to semantically filter market titles, e.g. points, score, over, NBA, player>"]
}
The keywords field is critical — extract the most specific terms from the user's intent that should appear in matching market titles.
Return ONLY the JSON, no markdown, no extra text."""
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 600, "system": system,
                  "messages": [{"role": "user", "content": user_input}]},
            timeout=15
        )
        r.raise_for_status()
        text = r.json()["content"][0]["text"].strip().replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)}

# ── stats fetching ───────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_nba_player_stats(player_name):
    """Fetch last 5 games for an NBA player via balldontlie API (free, no key)."""
    try:
        # Search for player
        search = requests.get(
            f"https://www.balldontlie.io/api/v1/players?search={player_name.replace(' ','%20')}&per_page=1",
            timeout=8
        ).json()
        if not search.get("data"): return None
        player = search["data"][0]
        pid = player["id"]
        # Get last 5 game stats
        stats = requests.get(
            f"https://www.balldontlie.io/api/v1/stats?player_ids[]={pid}&per_page=5&seasons[]=2024",
            timeout=8
        ).json()
        games = stats.get("data", [])
        if not games: return None
        rows = []
        for g in games:
            rows.append({
                "Date":  g.get("game", {}).get("date", "")[:10],
                "PTS":   g.get("pts", "-"),
                "REB":   g.get("reb", "-"),
                "AST":   g.get("ast", "-"),
                "MIN":   g.get("min", "-"),
            })
        return {"player": f"{player['first_name']} {player['last_name']}", "team": player.get("team", {}).get("full_name",""), "games": rows}
    except Exception:
        return None

def _score_str(v):
    """ESPN returns score as either a plain string/number or {'value':120,'displayValue':'120'}."""
    if isinstance(v, dict):
        return v.get("displayValue") or str(int(v["value"])) if "value" in v else "?"
    return str(v) if v not in (None, "", "?") else "?"

@st.cache_data(ttl=3600)
def fetch_espn_team_stats(team_name, sport="nba"):
    """Fetch last 5 completed games for a team via ESPN unofficial endpoint."""
    try:
        sport_map = {
            "nba":    ("basketball", "nba"),
            "nfl":    ("football",   "nfl"),
            "mlb":    ("baseball",   "mlb"),
            "nhl":    ("hockey",     "nhl"),
            "soccer": ("soccer",     "usa.1"),
        }
        s, league = sport_map.get(sport, ("basketball", "nba"))
        r = requests.get(
            f"https://site.api.espn.com/apis/site/v2/sports/{s}/{league}/teams?limit=100",
            timeout=8
        ).json()
        teams = r.get("sports",[{}])[0].get("leagues",[{}])[0].get("teams",[])
        match = next(
            (t["team"] for t in teams if team_name.lower() in t["team"]["displayName"].lower()),
            None
        )
        if not match: return None
        tid = match["id"]
        sched = requests.get(
            f"https://site.api.espn.com/apis/site/v2/sports/{s}/{league}/teams/{tid}/schedule",
            timeout=8
        ).json()
        completed = [
            e for e in sched.get("events", [])
            if e.get("competitions",[{}])[0].get("status",{}).get("type",{}).get("completed", False)
        ]
        rows = []
        for e in completed[-5:]:
            comp  = e.get("competitions",[{}])[0]
            comps = comp.get("competitors", [])
            home  = next((c for c in comps if c.get("homeAway") == "home"), {})
            away  = next((c for c in comps if c.get("homeAway") == "away"), {})
            tc    = next((c for c in comps if tid in str(c.get("team",{}).get("id",""))), {})
            rows.append({
                "Date":  e.get("date","")[:10],
                "Home":  home.get("team",{}).get("abbreviation","?"),
                "Away":  away.get("team",{}).get("abbreviation","?"),
                "Score": f"{_score_str(home.get('score'))}-{_score_str(away.get('score'))}",
                "W/L":   "W" if tc.get("winner") else "L",
            })
        return {"team": match["displayName"], "games": rows}
    except Exception:
        return None

@st.cache_data(ttl=3600)
def detect_entity_and_fetch_stats(market_title, category, sport_hint=""):
    """Given a market title, try to detect player/team and fetch relevant stats.
    sport_hint: output of get_sport_label() — e.g. '🏀 NBA'. Used for reliable sport routing."""
    if category != "Sports": return None
    title_lower = market_title.lower()

    # Detect sport — sport_hint from get_sport_label() is most reliable (uses Kalshi ticker prefix)
    if "NBA" in sport_hint or any(x in title_lower for x in [
        "nba","basketball",
        "lakers","celtics","warriors","bulls","heat","nuggets","bucks","pistons","thunder",
        "cavaliers","clippers","rockets","knicks","nets","hawks","magic","76ers","sixers",
        "raptors","jazz","spurs","suns","kings","timberwolves","grizzlies","blazers",
        "pelicans","hornets","pacers","wizards","mavericks","grizzlies",
    ]):
        sport = "nba"
    elif "NFL" in sport_hint or any(x in title_lower for x in [
        "nfl","football","chiefs","eagles","49ers","cowboys","patriots","rams","ravens",
        "broncos","packers","steelers","bears","giants","jets","dolphins","seahawks",
    ]):
        sport = "nfl"
    elif "MLB" in sport_hint or any(x in title_lower for x in [
        "mlb","baseball","yankees","dodgers","mets","cubs","red sox","astros","braves",
        "cardinals","giants","athletics","padres","phillies","twins","tigers","orioles",
    ]):
        sport = "mlb"
    elif "NHL" in sport_hint or any(x in title_lower for x in [
        "nhl","hockey","maple leafs","bruins","rangers","penguins","lightning","capitals",
        "oilers","avalanche","golden knights","hurricanes","flames","senators","canadiens",
    ]):
        sport = "nhl"
    else:
        sport = "nba"  # default

    import re as _re_stat

    # ── Game matchup detection: "Team A at Team B Winner?" ─────────────────────
    # Handles city-only names (Boston, Oklahoma City, Atlanta, Detroit) that
    # wouldn't match single-team keyword lookups.
    _at_m = _re_stat.search(r'^(.+?)\s+at\s+(.+?)(?:\s+(?:Winner|winner|Spread|Total)|\?|$)', market_title)
    if _at_m:
        team_a = _at_m.group(1).strip()
        team_b = _at_m.group(2).strip()
        stats_a = fetch_espn_team_stats(team_a, sport)
        stats_b = fetch_espn_team_stats(team_b, sport)
        if stats_a or stats_b:
            return {"type": "matchup", "sport": sport, "team_a": stats_a, "team_b": stats_b}

    # ── Single entity: player or team ─────────────────────────────────────────
    import re as _re_stat2

    # Strip trailing stat tokens so "LeBron James 20+ Points?" → "LeBron James"
    _clean_title = _re_stat2.sub(
        r'\b(\d+\+?|\d+[-–]\d+|points?|rebounds?|assists?|goals?|saves?|hits?|'
        r'yards?|touchdowns?|steals?|blocks?|shots?|over|under|scorer|winner|wins?)\b',
        '', market_title, flags=_re_stat2.IGNORECASE
    ).strip()

    words = _clean_title.split()
    candidates = []
    skip = {"Will","The","NBA","NFL","MLB","NHL","MLS","Who","What","How",
            "When","Does","Can","Is","Are","First","Last","Next","Top","Total"}
    for i in range(len(words)-1):
        if words[i][0].isupper() and words[i+1][0].isupper():
            pair = f"{words[i]} {words[i+1]}"
            if words[i] not in skip:
                candidates.append(pair)
    for i in range(len(words)-2):
        if words[i][0].isupper() and words[i+1][0].isupper() and words[i+2][0].isupper():
            triple = f"{words[i]} {words[i+1]} {words[i+2]}"
            if words[i] not in skip:
                candidates.append(triple)

    # Try player lookup — NBA first, then team lookup for non-NBA sports
    for candidate in candidates:
        stats = fetch_nba_player_stats(candidate)
        if stats: return {"type": "player", "sport": sport, **stats}

    for candidate in candidates:
        stats = fetch_espn_team_stats(candidate, sport)
        if stats: return {"type": "team", "sport": sport, **stats}

    return None

def _single_stats_table_html(team_stats, color):
    if not team_stats or not team_stats.get("games"): return ""
    games = team_stats["games"]
    headers = list(games[0].keys()) if games else []
    title = f"{team_stats['team']} · Last {len(games)} games"
    rows_html = "".join(
        "<tr>" + "".join(f"<td style='padding:6px 10px;border-bottom:1px solid #1e2530;color:#c5cad3;font-size:12px;'>{g.get(h,'-')}</td>" for h in headers) + "</tr>"
        for g in games
    )
    return f"""<div style='background:#14181e;border:1px solid #1e2530;border-left:3px solid {color};border-radius:1px;padding:12px 16px;margin-top:8px;font-family:'Geist Mono','Courier New',monospace;'>
<div style='font-size:10px;color:#666;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;'>{title}</div>
<table style='width:100%;border-collapse:collapse;'>
<thead><tr>{"".join(f"<th style='padding:4px 10px;text-align:left;font-size:10px;color:#999ea6;letter-spacing:0.06em;border-bottom:1px solid #1e2530;'>{h}</th>" for h in headers)}</tr></thead>
<tbody>{rows_html}</tbody></table></div>"""

def render_stats_card(stats):
    """Render a compact stats card as HTML."""
    if not stats: return ""

    # Matchup: two teams side by side
    if stats.get("type") == "matchup":
        html_a = _single_stats_table_html(stats.get("team_a"), "#F59E0B")
        html_b = _single_stats_table_html(stats.get("team_b"), "#3B82F6")
        if not html_a and not html_b: return ""
        return f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;'>{html_a}{html_b}</div>"

    games = stats.get("games", [])
    if not games: return ""

    if stats["type"] == "player":
        headers = ["Date","PTS","REB","AST","MIN"]
        title = f"{stats['player']} — {stats.get('team','')} · Last {len(games)} games"
        color = "#8B5CF6"
    else:
        headers = list(games[0].keys()) if games else []
        title = f"{stats['team']} · Last {len(games)} games"
        color = "#3B82F6"

    rows_html = ""
    for g in games:
        rows_html += "<tr>" + "".join(f"<td style='padding:6px 10px;border-bottom:1px solid #1e2530;color:#c5cad3;font-size:12px;'>{g.get(h,'-')}</td>" for h in headers) + "</tr>"

    return f"""
<div style='background:#14181e;border:1px solid #1e2530;border-left:3px solid {color};border-radius:1px;padding:12px 16px;margin-top:8px;font-family:'Geist Mono','Courier New',monospace;'>
<div style='font-size:10px;color:#666;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;'>{title}</div>
<table style='width:100%;border-collapse:collapse;'>
<thead><tr>{"".join(f"<th style='padding:4px 10px;text-align:left;font-size:10px;color:#999ea6;letter-spacing:0.06em;border-bottom:1px solid #1e2530;'>{h}</th>" for h in headers)}</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</div>"""

# ── load + split data ─────────────────────────────────────────────────────────
df_raw = load_data()
if df_raw.empty:
    st.warning("No data yet."); st.stop()

df_poly_raw   = df_raw[df_raw["source"] == "polymarket"]
df_kalshi_raw = df_raw[df_raw["source"] == "kalshi"]
df_live_raw   = df_raw[df_raw["source"].isin(["polymarket","kalshi"])]

df_poly_markets   = build_markets_df(df_poly_raw)   if not df_poly_raw.empty   else pd.DataFrame()
df_kalshi_markets = build_markets_df(df_kalshi_raw)  if not df_kalshi_raw.empty  else pd.DataFrame()
df_markets        = build_markets_df(df_live_raw)

# ── sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("## Callibr")
st.sidebar.markdown("<div style='font-size:11px;color:#636870;margin-bottom:16px;'>Find your edge</div>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Data freshness indicator
_last_ts_str = df_raw["timestamp"].max()
_last_ts     = pd.to_datetime(_last_ts_str, errors="coerce", utc=True)
_mins_ago    = int((pd.Timestamp.now(tz="UTC") - _last_ts).total_seconds() / 60) if pd.notna(_last_ts) else 999
if _mins_ago <= 15:
    _fc, _fl = "#00C2A8", "LIVE"
elif _mins_ago <= 60:
    _fc, _fl = "#F59E0B", f"{_mins_ago}m ago"
else:
    _fc, _fl = "#DC2626", f"{_mins_ago // 60}h ago"

st.sidebar.markdown(f"""
<div style='background:#14181e;border:1px solid #1e2530;border-radius:2px;padding:12px 14px;margin-bottom:10px;'>
  <div style='font-size:9px;color:#999ea6;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;'>Data Pipeline</div>
  <div style='display:flex;justify-content:space-between;align-items:center;'>
    <span style='font-size:22px;font-weight:700;color:#eef2f9;'>{len(df_raw):,}</span>
    <span style='font-size:10px;color:#999ea6;'>snapshots</span>
  </div>
  <div style='margin-top:8px;display:flex;align-items:center;gap:6px;'>
    <span style='width:8px;height:8px;border-radius:50%;background:{_fc};display:inline-block;'></span>
    <span style='font-size:11px;color:{_fc};font-weight:600;'>{_fl}</span>
    <span style='font-size:10px;color:#636870;'>· {_last_ts_str[:16] if _last_ts_str else "—"}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# Source split
_n_poly   = df_raw[df_raw["source"] == "polymarket"]["ticker"].nunique()
_n_kalshi = df_raw[df_raw["source"] == "kalshi"]["ticker"].nunique()
_n_total  = _n_poly + _n_kalshi
_poly_pct   = int(_n_poly  / _n_total * 100) if _n_total > 0 else 0
_kalshi_pct = 100 - _poly_pct

st.sidebar.markdown(f"""
<div style='background:#14181e;border:1px solid #1e2530;border-radius:2px;padding:12px 14px;margin-bottom:10px;'>
  <div style='font-size:9px;color:#999ea6;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px;'>Sources</div>
  <div style='display:flex;justify-content:space-between;margin-bottom:4px;'>
    <span style='font-size:11px;color:#8B5CF6;font-weight:600;'>🟣 Polymarket</span>
    <span style='font-size:12px;color:#eef2f9;font-weight:700;'>{_n_poly:,}</span>
  </div>
  <div style='background:#1c2028;border-radius:4px;height:4px;margin-bottom:8px;overflow:hidden;'>
    <div style='background:#8B5CF6;height:4px;width:{_poly_pct}%;border-radius:4px;'></div>
  </div>
  <div style='display:flex;justify-content:space-between;margin-bottom:4px;'>
    <span style='font-size:11px;color:#3B82F6;font-weight:600;'>🔵 Kalshi</span>
    <span style='font-size:12px;color:#eef2f9;font-weight:700;'>{_n_kalshi:,}</span>
  </div>
  <div style='background:#1c2028;border-radius:4px;height:4px;overflow:hidden;'>
    <div style='background:#3B82F6;height:4px;width:{_kalshi_pct}%;border-radius:4px;'></div>
  </div>
</div>
""", unsafe_allow_html=True)

# Mini category bar chart
_cat_counts = df_markets["category"].value_counts().reset_index()
_cat_counts.columns = ["Category", "Count"]
_cat_counts["Category"] = _cat_counts["Category"].replace(
    {"Politics & Macro": "Politics", "Entertainment & Legal": "Entmt/Legal", "Tech & Markets": "Tech"}
)
_fig_sb = px.bar(_cat_counts, x="Count", y="Category", orientation="h", color_discrete_sequence=["#3B82F6"])
_fig_sb.update_traces(hovertemplate="<b>%{y}</b><br>%{x} markets<extra></extra>")
apply_layout(_fig_sb, "Markets by Category", height=220)
_fig_sb.update_layout(margin=dict(l=4, r=4, t=28, b=4), yaxis=dict(tickfont=dict(size=9)))
st.sidebar.plotly_chart(_fig_sb, use_container_width=True)

# ── tabs ──────────────────────────────────────────────────────────────────────
tab1, tab4, tab2 = st.tabs([
    "📊 Overview", "🔍 Market Research", "🔀 Sources"
])

# ── edge score helpers (defined here so tab1 + tab4 can both use them) ───────
_NOISE_PATTERNS = [
    "first half", "1st half", "second half", "2nd half",
    "first quarter", "1st quarter", "second quarter", "2nd quarter",
    "third quarter", "3rd quarter", "fourth quarter", "4th quarter",
    "first period", "1st period", "second period", "2nd period", "third period", "3rd period",
    "halftime", "half time", "half-time",
    "next goal", "next score", "next basket", "next point", "next touchdown",
    "next team to score", "anytime scorer",
    "announcer", "will the announcer", "commentator",
    "will anyone say", "will a player say", "will the broadcast",
    "will the crowd", "will fans",
    "celebration", "will celebrate", "dunk celebration",
    "will shake hands", "will hug",
    "will be ejected", "will get ejected", "will be removed",
    "live ", "in-game", "in game",
]
_SIGNAL_PATTERNS = [
    "winner", "win the", "will win",
    "total points", "total goals", "total score",
    "spread", "cover", "over/under", "over under",
    "moneyline", "money line",
    "advance", "qualify", "make the",
    "championship", "finals", "playoffs", "postseason",
    "mvp", "most valuable",
    "season wins", "win total",
]

def compute_edge_score(row, cat_avg_changes):
    cp = row.get("current_price", 0.5)
    title = row.get("event_ticker", "").lower()
    if cp <= 0.15 or cp >= 0.85:
        return 0
    if any(p in title for p in _NOISE_PATTERNS):
        return 10 if " vs " in title else 0
    score = 40.0
    mid = row.get("mid_price", cp)
    divergence = abs(cp - mid)
    score += min(divergence * 80, 25)
    cat = row.get("category", "Other")
    cat_avg_change = cat_avg_changes.get(cat, 0)
    own_change = row.get("price_change_pct", 0)
    drift_delta = abs(own_change - cat_avg_change)
    score += min(drift_delta * 0.6, 15)
    if cp < 0.25 or cp > 0.75:
        score += 8
    elif 0.38 <= cp <= 0.62:
        score -= 8
    if any(p in title for p in _SIGNAL_PATTERNS):
        score += 10
    days = row.get("days_to_close", 30)
    if days is not None and not pd.isna(days):
        if days <= 3:    score += 12
        elif days <= 7:  score += 7
        elif days <= 14: score += 3
    snap = row.get("snapshot_count", 1)
    if snap >= 5: score += 5
    elif snap <= 1: score -= 5
    return min(max(round(score), 0), 100)

def compute_edge_score_breakdown(row, cat_avg_changes):
    """Returns a dict of labelled component contributions for display."""
    cp    = row.get("current_price", 0.5)
    title = row.get("event_ticker", "").lower()
    parts = {}
    parts["Base"] = 40
    mid       = row.get("mid_price", cp)
    div       = abs(cp - mid)
    parts["Divergence"] = round(min(div * 80, 25))
    cat            = row.get("category", "Other")
    cat_avg_change = cat_avg_changes.get(cat, 0)
    own_change     = row.get("price_change_pct", 0)
    parts["Drift vs category"] = round(min(abs(own_change - cat_avg_change) * 0.6, 15))
    if cp < 0.25 or cp > 0.75:
        parts["Price zone"] = 8
    elif 0.38 <= cp <= 0.62:
        parts["Price zone"] = -8
    else:
        parts["Price zone"] = 0
    parts["Signal keywords"] = 10 if any(p in title for p in _SIGNAL_PATTERNS) else 0
    days = row.get("days_to_close", 30)
    if days is not None and not pd.isna(days):
        parts["Urgency"] = 12 if days <= 3 else (7 if days <= 7 else (3 if days <= 14 else 0))
    else:
        parts["Urgency"] = 0
    snap = row.get("snapshot_count", 1)
    parts["Liquidity"] = 5 if snap >= 5 else (-5 if snap <= 1 else 0)
    return parts

def extract_event_group(title):
    """Strip outcome token to get the parent event name (used for game_key grouping)."""
    import re
    t = title.strip()
    t = re.sub(r'\?\s*$', '', t).strip()
    t = re.sub(r'\s*\(.*?\)\s*$', '', t).strip()
    t = re.sub(r'\b(winner|to win|wins|spread|moneyline|total|over|under|by \d[\d-]*)\s*$', '', t, flags=re.IGNORECASE).strip()
    return t if t else title

def extract_game_key_global(ticker, event_ticker):
    """Extract stable game key from Kalshi tickers; falls back to normalised event title."""
    import re as _re
    if ticker and isinstance(ticker, str):
        m = _re.search(r'(\d{2}(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\d{2})([A-Z]{6})', ticker.upper())
        if m:
            return m.group(0)
    return extract_event_group(event_ticker)

_SPORT_LABELS = {
    "KXNBAGAME":    "🏀 NBA",   "KXNBA":       "🏀 NBA",
    "KXNHLGAME":    "🏒 NHL",   "KXNHL":       "🏒 NHL",
    "KXMLBGAME":    "⚾ MLB",   "KXMLB":       "⚾ MLB",
    "KXNFLGAME":    "🏈 NFL",   "KXNFL":       "🏈 NFL",
    "KXEPLGAME":    "⚽ EPL",   "KXEPL":       "⚽ EPL",
    "KXUCLGAME":    "⚽ UCL",   "KXUCL":       "⚽ UCL",
    "KXMLSGAME":    "⚽ MLS",   "KXMLS":       "⚽ MLS",
    "KXNCAABBGAME": "🏀 NCAAB", "KXNCAAB":     "🏀 NCAAB",
    "KXNCAAWBGAME": "🏀 NCAAW",
    "KXLALIGAGAME": "⚽ La Liga","KXLALIGA":    "⚽ La Liga",
    "KXLALIGA2GAME":"⚽ La Liga 2",
    "KXCBAGAME":    "🏀 CBA",
    "KXIPLGAME":    "🏏 IPL",
    "KXFIFAGAME":   "⚽ FIFA",
    "KXATPMATCH":   "🎾 ATP",   "KXWTAMATCH":  "🎾 WTA",
    "KXATPCHALLENGERMATCH": "🎾 ATP Challenger",
    "KXCS2GAME":    "🎮 CS2",
    "KXCODGAME":    "🎮 CoD",
}

_SPORT_TITLE_KEYWORDS = [
    # (label, must-contain-any, must-not-contain-any)
    ("🏀 NBA",        ["nba","basketball"," lakers"," celtics"," warriors"," knicks"," nets",
                       " bulls"," heat"," nuggets"," bucks"," suns"," clippers"," rockets",
                       " sixers"," raptors"," maverick"," grizzl"," pelicans"," spurs",
                       " pacers"," pistons"," cavaliers"," hawks"," magic"," hornets",
                       " wizards"," thunder"," timberwolves"," jazz"," blazers"," kings",
                       " golden state"," los angeles l"," los angeles c"], ["nhl","ncaa"]),
    ("🏈 NFL",        ["nfl"," super bowl"," touchdown"," quarterback"," nfl "," chiefs",
                       " patriots"," cowboys"," eagles"," steelers"," 49ers"," ravens",
                       " bengals"," bills"," dolphins"," jets"," broncos"," raiders",
                       " chargers"," colts"," titans"," jaguars"," texans"," browns",
                       " bears"," packers"," vikings"," lions"," falcons"," panthers",
                       " saints"," buccaneers"," cardinals"," rams"," seahawks"], ["nba","nhl","mlb"]),
    ("🏒 NHL",        ["nhl","stanley cup","hockey"," bruins"," rangers"," maple leafs",
                       " canadiens"," penguins"," flyers"," capitals"," lightning",
                       " panthers nhl"," hurricanes"," devils"," islanders"," senators",
                       " sabres"," red wings"," blue jackets"," predators"," blues",
                       " avalanche"," stars nhl"," wild"," jets nhl"," flames"," oilers",
                       " canucks"," sharks"," ducks"," coyotes"," golden knights"," kraken"], []),
    ("⚾ MLB",        ["mlb","baseball"," world series"," home run"," pitcher"," innings",
                       " yankees"," red sox"," dodgers"," cubs"," cardinals mlb"," braves",
                       " mets"," phillies"," nationals"," marlins"," astros"," rangers mlb",
                       " athletics"," angels"," mariners"," padres"," giants mlb",
                       " rockies"," diamondbacks"," brewers"," twins"," white sox",
                       " tigers"," indians"," guardians"," royals"," blue jays"," rays",
                       " orioles"], []),
    ("🏀 NCAAB",      ["ncaa basketball","march madness","ncaab","college basketball"], []),
    ("🏈 NCAAF",      ["ncaa football","college football","ncaaf"], []),
    ("⚽ EPL",        ["premier league","epl"," arsenal"," chelsea"," liverpool"," manchester",
                       " tottenham"," everton"," newcastle"," aston villa"," west ham",
                       " leicester"," wolves"," fulham"," brentford"," brighton"], ["la liga","bundesliga","serie a","ligue 1"]),
    ("⚽ UCL",        ["champions league","ucl"], []),
    ("⚽ MLS",        ["mls","major league soccer"], []),
    ("⚽ La Liga",    ["la liga"," real madrid"," barcelona"," atletico"," sevilla"," valencia",
                       " villarreal"," athletic bilbao"," real sociedad"," betis"], []),
    ("⚽ Bundesliga", ["bundesliga"," bayern"," dortmund"," leverkusen"," frankfurt",
                       " gladbach"," union berlin"," freiburg"], []),
    ("⚽ Serie A",    ["serie a"," juventus"," inter milan"," ac milan"," napoli"," roma",
                       " lazio"," atalanta"], []),
    ("⚽ FIFA",       ["world cup","fifa"], []),
    ("🎾 ATP",        ["atp","tennis"," djokovic"," alcaraz"," sinner"," medvedev"," zverev",
                       " federer"," nadal"], ["wta"]),
    ("🎾 WTA",        ["wta"," swiatek"," sabalenka"," gauff"," rybakina"], []),
    ("🏏 Cricket",    ["cricket","ipl","test match"," ashes"], []),
    ("🥊 Boxing/MMA", ["boxing","ufc","mma","fight","bout"," knockout"], []),
    ("🏌️ Golf",       ["golf","pga","masters","open championship","ryder cup"," tiger woods"], []),
    ("🏎️ F1",         ["formula 1","formula one","f1 ","grand prix"," verstappen"," hamilton f1"], []),
    ("🏀 EuroLeague", ["euroleague","eurocup"], []),
    ("⚽ Ligue 1",    ["ligue 1"," psg"," paris saint"], []),
    ("🎮 Esports",    ["esports","cs2","counter-strike","valorant","league of legends",
                       "call of duty","cod league","overwatch"], []),
]

def get_sport_label(ticker, event_ticker=""):
    """Return sport emoji + league from Kalshi ticker prefix or title keywords."""
    if ticker and isinstance(ticker, str):
        t = ticker.upper()
        for prefix in sorted(_SPORT_LABELS, key=len, reverse=True):
            if t.startswith(prefix):
                return _SPORT_LABELS[prefix]
    # Fallback: infer from event title keywords (covers Polymarket)
    title = (event_ticker or "").lower()
    if not title:
        return ""
    for label, keywords, excludes in _SPORT_TITLE_KEYWORDS:
        if excludes and any(ex in title for ex in excludes):
            continue
        if any(kw in title for kw in keywords):
            return label
    return ""

def edge_score_color(score):
    if score >= 75: return "#00C2A8"
    elif score >= 55: return "#F59E0B"
    else: return "#555555"

def edge_score_label(score):
    if score >= 75: return "STRONG EDGE"
    elif score >= 55: return "MODERATE"
    else: return "WEAK"

# ── Upgrade "Other" → "Sports" wherever get_sport_label detects a sport ──────
# categorize() only sees the title text, so Kalshi game markets like
# "Atlanta at Detroit Winner?" fall through to "Other".  Re-label them here
# using the full ticker prefix lookup so every table and filter is correct.
for _df_fix in [df_markets, df_poly_markets, df_kalshi_markets]:
    if _df_fix.empty:
        continue
    _mask = (_df_fix["category"] == "Other") & _df_fix.apply(
        lambda r: bool(get_sport_label(r.get("ticker", ""), r.get("event_ticker", ""))), axis=1
    )
    _df_fix.loc[_mask, "category"] = "Sports"

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown(
        f"## Market Overview &nbsp;&nbsp;"
        f"<span style='border:1px solid {_fc};color:{_fc};font-size:9px;font-weight:700;"
        f"padding:2px 8px;border-radius:1px;vertical-align:middle;letter-spacing:0.1em;'>{_fl}</span>"
        f"<span style='color:#636870;font-size:11px;margin-left:8px;vertical-align:middle;'>"
        f"updated {_last_ts_str[:16] if _last_ts_str else '—'} UTC</span>",
        unsafe_allow_html=True
    )

    f1, f2, f3, f4 = st.columns(4)
    with f1: min_prob = st.slider("Min probability", 0.0, 1.0, 0.05, 0.05, key="ov_min")
    with f2: max_prob = st.slider("Max probability", 0.0, 1.0, 0.95, 0.05, key="ov_max")
    with f3: category_filter = st.selectbox("Category", ["All"]+sorted(df_markets["category"].unique().tolist()), key="ov_cat")
    with f4: sort_by = st.selectbox("Sort by", ["Opening Price","Current Price","Price Change","Days to Close"], key="ov_sort")

    df = df_markets.copy()
    df = df[(df["mid_price"] >= min_prob) & (df["mid_price"] <= max_prob)]
    if category_filter != "All": df = df[df["category"] == category_filter]
    sort_map = {"Opening Price":"mid_price","Current Price":"current_price","Price Change":"price_change","Days to Close":"days_to_close"}
    df = df.sort_values(sort_map[sort_by], ascending=False).reset_index(drop=True)

    st.markdown("---")
    # Split upcoming vs long-term for accurate metrics
    df_upcoming = df[df["days_to_close"].between(0, 30)]
    df_longterm  = df[df["days_to_close"] > 30]
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Markets tracked",      f"{len(df):,}")
    c2.metric("Closing ≤30 days",     f"{len(df_upcoming):,}")
    c3.metric("Biggest mover",        f"{df['price_change_pct'].abs().max():.0f}%" if not df.empty else "N/A")
    c4.metric("Categories",           df["category"].nunique())
    c5,c6,c7,c8 = st.columns(4)
    c5.metric("Avg current price",    f"{df['current_price'].mean():.2%}")
    c6.metric("Avg days (upcoming)",  f"{df_upcoming['days_to_close'].mean():.0f}d" if not df_upcoming.empty else "N/A")
    c7.metric("Avg days (long-term)", f"{df_longterm['days_to_close'].mean():.0f}d" if not df_longterm.empty else "N/A")
    c8.metric("Markets moving",       f"↑{len(df[df['price_change']>0]):,} ↓{len(df[df['price_change']<0]):,}")

    st.markdown("---")
    st.markdown("### Prediction Market Intelligence")
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        bins   = [0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.0]
        blabs  = ["0-10%","10-20%","20-30%","30-40%","40-50%","50-60%","60-70%","70-80%","80-90%","90-100%"]
        df["bucket"] = pd.cut(df["mid_price"], bins=bins, labels=blabs)
        bdata = df["bucket"].value_counts().sort_index().reset_index()
        bdata.columns = ["Bucket","Count"]
        fig = px.bar(bdata, x="Bucket", y="Count", color_discrete_sequence=["#3B82F6"])
        fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y} markets<extra></extra>")
        apply_layout(fig, "Probability Buckets")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        sentiment = pd.DataFrame({
            "Type":  ["Strong YES (>80%)", "Strong NO (<20%)", "Contested (40-60%)"],
            "Count": [len(df[df["current_price"]>0.8]),
                      len(df[df["current_price"]<0.2]),
                      len(df[(df["current_price"]>=0.4)&(df["current_price"]<=0.6)])]
        })
        fig2 = px.bar(sentiment, x="Type", y="Count",
                      color="Type", color_discrete_map={
                          "Strong YES (>80%)":"#00C2A8",
                          "Strong NO (<20%)":"#DC2626",
                          "Contested (40-60%)":"#F59E0B"})
        fig2.update_traces(hovertemplate="<b>%{x}</b><br>%{y} markets<extra></extra>")
        fig2.update_layout(showlegend=False)
        apply_layout(fig2, "Market Sentiment")
        st.plotly_chart(fig2, use_container_width=True)

    with col_c:
        drift = df.groupby("category")["price_change_pct"].mean().sort_values().reset_index()
        drift.columns = ["Category","Avg Change %"]
        drift["Color"] = drift["Avg Change %"].apply(lambda x: "#00C2A8" if x >= 0 else "#DC2626")
        fig3 = px.bar(drift, x="Avg Change %", y="Category", orientation="h",
                      color="Color", color_discrete_map="identity")
        fig3.add_vline(x=0, line_color="#333333", line_width=1)
        fig3.update_traces(hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>")
        fig3.update_layout(showlegend=False)
        apply_layout(fig3, "Price Drift by Category")
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # Scatter — opening vs current, colour by source
    fig_sc = go.Figure()
    for src in ["polymarket","kalshi"]:
        sub = df[df["source"]==src] if "source" in df.columns else pd.DataFrame()
        if not sub.empty:
            fig_sc.add_trace(go.Scatter(
                x=sub["mid_price"], y=sub["current_price"],
                mode="markers",
                marker=dict(color=SOURCE_COLORS[src], size=5, opacity=0.5),
                name=SOURCE_LABELS[src],
                hovertemplate="<b>%{text}</b><br>Open: %{x:.2%}<br>Current: %{y:.2%}<extra></extra>",
                text=sub["event_ticker"].str[:50]
            ))
    fig_sc.add_trace(go.Scatter(x=[0,1], y=[0,1], mode="lines",
                                line=dict(color="#333333", dash="dash", width=1),
                                name="No change", hoverinfo="skip"))
    fig_sc.update_xaxes(tickformat=".0%")
    fig_sc.update_yaxes(tickformat=".0%")
    apply_layout(fig_sc, "Opening vs Current Price", height=380)
    st.plotly_chart(fig_sc, use_container_width=True)

    st.markdown("---")
    # Filter skewed markets from all table sections below (charts/metrics above use unfiltered df)
    df_tables     = filter_skewed(df)
    _cat_avg_tab1 = df_markets.groupby("category")["price_change_pct"].mean().to_dict()

    st.markdown("### 🔥 Biggest Price Movers")
    top_movers = df_markets.nlargest(10,"price_change_pct")[
        ["event_ticker","source","category","current_price","price_change_pct"]].copy()
    top_movers["source"]        = top_movers["source"].map(SOURCE_LABELS).fillna(top_movers["source"])
    top_movers["Resolves YES"]  = top_movers["current_price"].apply(lambda x: f"{x*100:.0f}%")
    top_movers["Latest Change"] = top_movers["price_change_pct"].apply(lambda x: f"+{x:.1f}%" if x >= 0 else f"{x:.1f}%")
    top_movers = top_movers[["event_ticker","source","category","Resolves YES","Latest Change"]]
    top_movers.columns = ["Market","Source","Category","Resolves YES","Latest Change"]
    st.dataframe(top_movers.reset_index(drop=True), use_container_width=True)

    st.markdown("---")
    # ── helper to render a sortable, downloadable market table ───────────────
    def render_market_table(df_t, table_key="tbl"):
        if df_t.empty:
            st.info("No markets match current filters.")
            return
        disp = df_t[["source","category","event_ticker","current_price","price_change_pct","days_to_close"]].copy()
        disp["Source"] = disp["source"].map(SOURCE_LABELS).fillna(disp["source"])
        disp = disp[["Source","category","event_ticker","current_price","price_change_pct","days_to_close"]]
        disp.columns = ["Source","Category","Market","Resolves YES","Change %","Days to Close"]
        st.dataframe(
            disp.reset_index(drop=True),
            use_container_width=True,
            column_config={
                "Resolves YES": st.column_config.NumberColumn("Resolves YES", format="%.0f%%", min_value=0, max_value=1),
                "Change %":     st.column_config.NumberColumn("Change %",     format="%.1f%%"),
                "Days to Close":st.column_config.NumberColumn("Days to Close",format="%d d"),
            }
        )
        st.download_button(
            "⬇ Download CSV", disp.to_csv(index=False).encode(),
            file_name="callibr_markets.csv", mime="text/csv", key=f"dl_{table_key}"
        )

    # ── Closing Soon — Next 14 Days ──────────────────────────────────────────
    _closing_soon = df_tables[df_tables["days_to_close"].between(0, 14)].copy()
    if not _closing_soon.empty:
        _closing_soon["edge_score"] = _closing_soon.apply(
            lambda r: compute_edge_score(r, _cat_avg_tab1), axis=1
        )
        _closing_soon["game_key"] = _closing_soon.apply(
            lambda r: extract_game_key_global(r["ticker"], r["event_ticker"]), axis=1
        )
        st.markdown(
            f"### 🔥 Closing Soon — Next 14 Days "
            f"<span style='font-size:14px;color:#999ea6;font-weight:400;'>({len(_closing_soon):,} markets)</span>",
            unsafe_allow_html=True
        )

        # ── Sports Games: one card per game ──────────────────────────────────
        _sports_cs = _closing_soon[_closing_soon["category"] == "Sports"]
        if not _sports_cs.empty:
            st.caption("🏆 Sports games — grouped by match, sorted by urgency")
            _sports_gm = (
                _sports_cs.groupby("game_key", sort=False)
                .agg(
                    best_edge=("edge_score", "max"),
                    n_markets=("ticker", "count"),
                    min_days=("days_to_close", "min"),
                    event_title=("event_ticker", "first"),
                    source=("source", "first"),
                )
                .sort_values(["min_days", "best_edge"], ascending=[True, False])
            )
            for _gk, _gm in _sports_gm.iterrows():
                _grp    = _sports_cs[_sports_cs["game_key"] == _gk]
                _winner = _grp[_grp["event_ticker"].str.contains("Winner|winner", na=False)]
                _gtitle = _winner.iloc[0]["event_ticker"] if not _winner.empty else _gm["event_title"]
                _md     = int(_gm["min_days"])
                _badge  = " 🟢 TODAY" if _md <= 0 else (" 🟡 TOMORROW" if _md == 1 else
                          (" 🟡 THIS WEEK" if _md <= 6 else ""))
                _sport  = get_sport_label(_grp.iloc[0]["ticker"], _grp.iloc[0]["event_ticker"]) if not _grp.empty else ""
                _sport_tag = f"[{_sport}]  " if _sport else ""
                _label  = f"{_sport_tag}{_gtitle}{_badge}  ·  {_md}d  ·  {int(_gm['n_markets'])} markets  ·  Edge {int(_gm['best_edge'])}"
                with st.expander(_label, expanded=(_md <= 1)):
                    _grp_disp = _grp[["event_ticker","current_price","price_change_pct","days_to_close","edge_score"]].copy()
                    _grp_disp.columns = ["Market","Resolves YES","Change %","Days","Edge"]
                    st.dataframe(
                        _grp_disp.reset_index(drop=True), use_container_width=True,
                        column_config={
                            "Resolves YES": st.column_config.NumberColumn(format="%.0f%%", min_value=0, max_value=1),
                            "Change %":     st.column_config.NumberColumn(format="%.1f%%"),
                            "Days":         st.column_config.NumberColumn(format="%d d"),
                            "Edge":         st.column_config.NumberColumn(format="%d"),
                        }
                    )

        # ── Other categories: flat sorted table ──────────────────────────────
        _other_cs = _closing_soon[_closing_soon["category"] != "Sports"].sort_values(
            ["days_to_close", "edge_score"], ascending=[True, False]
        )
        if not _other_cs.empty:
            st.caption("📋 All other categories — click column headers to sort")
            _cs_disp = _other_cs[["source","category","event_ticker","current_price","price_change_pct","days_to_close","edge_score"]].copy()
            _cs_disp["Source"] = _cs_disp["source"].map(SOURCE_LABELS).fillna(_cs_disp["source"])
            _cs_disp = _cs_disp[["Source","category","event_ticker","current_price","price_change_pct","days_to_close","edge_score"]]
            _cs_disp.columns = ["Source","Category","Market","Resolves YES","Change %","Days to Close","Edge"]
            st.dataframe(
                _cs_disp.reset_index(drop=True), use_container_width=True,
                column_config={
                    "Resolves YES":  st.column_config.NumberColumn("Resolves YES", format="%.0f%%", min_value=0, max_value=1),
                    "Change %":      st.column_config.NumberColumn("Change %",     format="%.1f%%"),
                    "Days to Close": st.column_config.NumberColumn("Days to Close",format="%d d"),
                    "Edge":          st.column_config.NumberColumn("Edge Score",   format="%d"),
                }
            )
            st.download_button(
                "⬇ Download CSV", _cs_disp.to_csv(index=False).encode(),
                file_name="callibr_closing_soon.csv", mime="text/csv", key="dl_closing_soon"
            )
        st.markdown("---")

    # Split into upcoming (≤30 days) and long-term (>30 days)
    upcoming = df_tables[df_tables["days_to_close"].between(0, 30)].sort_values("days_to_close", ascending=True)
    longterm  = df_tables[df_tables["days_to_close"] > 30].sort_values("days_to_close", ascending=True)
    no_date   = df_tables[df_tables["days_to_close"].isna()]

    # ── Upcoming ─────────────────────────────────────────────────────────────
    st.markdown(f"### ⚡ Upcoming — Next 30 Days &nbsp;<span style='font-size:14px;color:#999ea6;font-weight:400;'>({len(upcoming):,} markets)</span>", unsafe_allow_html=True)
    st.caption("Sorted by urgency — closest to closing first.")
    render_market_table(upcoming, "upcoming")

    st.markdown("---")

    # ── Long-term ─────────────────────────────────────────────────────────────
    with st.expander(f"📅  Long-term Markets — 30+ Days  ({len(longterm):,} markets)", expanded=False):
        st.caption("Sorted by closest close date first.")
        render_market_table(longterm, "longterm")

    # ── No close date ─────────────────────────────────────────────────────────
    if not no_date.empty:
        with st.expander(f"❔  No Close Date  ({len(no_date):,} markets)", expanded=False):
            render_market_table(no_date, "nodate")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — SOURCES
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("## Polymarket vs Kalshi")

    def source_panel(col, df_src, label, color):
        with col:
            st.markdown(f"#### {label}")
            if df_src.empty: st.info("No data yet."); return
            m1,m2,m3 = st.columns(3)
            m1.metric("Markets",        f"{len(df_src):,}")
            m2.metric("Avg probability", f"{df_src['current_price'].mean():.2%}")
            m3.metric("Moving up",       f"{len(df_src[df_src['price_change']>0]):,}")

            bins   = [0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.0]
            blabs  = ["0-10%","10-20%","20-30%","30-40%","40-50%","50-60%","60-70%","70-80%","80-90%","90-100%"]
            bkts   = pd.cut(df_src["current_price"], bins=bins, labels=blabs).value_counts().sort_index().reset_index()
            bkts.columns = ["Bucket","Count"]
            fig = px.bar(bkts, x="Bucket", y="Count", color_discrete_sequence=[color])
            fig.update_traces(hovertemplate="<b>%{x}</b><br>%{y} markets<extra></extra>")
            apply_layout(fig, "Probability Distribution", height=260)
            st.plotly_chart(fig, use_container_width=True)

            cats = df_src["category"].value_counts().reset_index()
            cats.columns = ["Category","Count"]
            fig2 = px.bar(cats, x="Count", y="Category", orientation="h", color_discrete_sequence=[color])
            fig2.update_traces(hovertemplate="<b>%{y}</b><br>%{x} markets<extra></extra>")
            apply_layout(fig2, "Markets by Category", height=260)
            st.plotly_chart(fig2, use_container_width=True)

            drift = df_src.groupby("category")["price_change_pct"].mean().sort_values().reset_index()
            drift.columns = ["Category","Avg Change %"]
            drift["Color"] = drift["Avg Change %"].apply(lambda x: "#00C2A8" if x>=0 else "#DC2626")
            fig3 = px.bar(drift, x="Avg Change %", y="Category", orientation="h",
                          color="Color", color_discrete_map="identity")
            fig3.add_vline(x=0, line_color="#333333", line_width=1)
            fig3.update_traces(hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>")
            fig3.update_layout(showlegend=False)
            apply_layout(fig3, "Price Drift by Category", height=260)
            st.plotly_chart(fig3, use_container_width=True)

    lc, rc = st.columns(2)
    source_panel(lc, df_poly_markets,   "🟣 Polymarket",    SOURCE_COLORS["polymarket"])
    source_panel(rc, df_kalshi_markets, "🔵 Kalshi (live)", SOURCE_COLORS["kalshi"])

    # ── Cross-exchange arbitrage detection ────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⚡ Cross-Exchange Opportunities")
    st.caption("Same event priced differently on Polymarket vs Kalshi. Larger gap = bigger potential edge.")

    import re as _re_arb

    def _normalise(title):
        """Lowercase, strip punctuation and common boilerplate for fuzzy matching."""
        t = title.lower()
        t = _re_arb.sub(r'[^a-z0-9 ]', ' ', t)
        stops = {"will","the","a","an","in","of","to","by","for","at","on","is","are",
                 "does","do","who","what","when","win","wins","winner","be"}
        return " ".join(w for w in t.split() if w not in stops and len(w) > 1)

    _poly_k   = df_poly_markets.copy()
    _kals_k   = df_kalshi_markets.copy()
    _poly_k["_norm"] = _poly_k["event_ticker"].apply(_normalise)
    _kals_k["_norm"] = _kals_k["event_ticker"].apply(_normalise)

    # Keep only the most recent price per ticker on each exchange
    _poly_k = _poly_k.sort_values("current_price").drop_duplicates("_norm", keep="last")
    _kals_k = _kals_k.sort_values("current_price").drop_duplicates("_norm", keep="last")

    # Exact normalised-title match
    _arb = _poly_k.merge(_kals_k, on="_norm", suffixes=("_poly","_kals"))
    if not _arb.empty:
        _arb["poly_price"]  = _arb["current_price_poly"]
        _arb["kals_price"]  = _arb["current_price_kals"]
        _arb["gap"]         = (_arb["poly_price"] - _arb["kals_price"]).abs()
        _arb["direction"]   = _arb.apply(
            lambda r: f"🟣 Poly higher by {r['gap']:.0%}" if r["poly_price"] > r["kals_price"]
                      else f"🔵 Kalshi higher by {r['gap']:.0%}", axis=1
        )
        _arb = _arb[_arb["gap"] >= 0.03].sort_values("gap", ascending=False)

        if not _arb.empty:
            _arb_disp = _arb[["event_ticker_poly","poly_price","kals_price","gap","direction"]].copy()
            _arb_disp.columns = ["Market","Poly %","Kalshi %","Gap","Direction"]
            st.dataframe(
                _arb_disp.reset_index(drop=True), use_container_width=True,
                column_config={
                    "Poly %":   st.column_config.NumberColumn(format="%.0f%%", min_value=0, max_value=1),
                    "Kalshi %": st.column_config.NumberColumn(format="%.0f%%", min_value=0, max_value=1),
                    "Gap":      st.column_config.NumberColumn("Gap", format="%.0f%%"),
                }
            )
            st.download_button(
                "⬇ Download CSV", _arb_disp.to_csv(index=False).encode(),
                file_name="callibr_arb.csv", mime="text/csv", key="dl_arb"
            )
        else:
            st.info("No cross-exchange gaps ≥3% found right now.")
    else:
        st.info("No exact title matches found across exchanges. Markets may be titled differently.")



# ─────────────────────────────────────────────────────────────────────────────
# EDGE SCORE + NEWS + RESEARCH CARD FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def enrich_title_with_context(title, ticker, close_time):
    """
    Parse Kalshi ticker to extract game matchup.
    Format: KXNBA3PT-26MAR10BOSSAS-BOSJBROWN7-4
      - 26MAR10BOSSAS = Mar 10, BOS vs SAS (two 3-letter codes concatenated)
    """
    import re
    if not ticker or not isinstance(ticker, str):
        return title
    if " vs " in title.lower():
        return title

    t = ticker.upper()

    # Find segment containing date — e.g. "26MAR10BOSSAS"
    date_seg_match = re.search(r'(\d{2}(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\d{2})([A-Z]+)?', t)
    if not date_seg_match:
        return title

    month_names = {"JAN":"Jan","FEB":"Feb","MAR":"Mar","APR":"Apr","MAY":"May","JUN":"Jun",
                   "JUL":"Jul","AUG":"Aug","SEP":"Sep","OCT":"Oct","NOV":"Nov","DEC":"Dec"}
    date_part = date_seg_match.group(1)  # e.g. "26MAR10"
    team_str  = date_seg_match.group(2) or ""  # e.g. "BOSSAS"

    # Parse date
    d_match = re.match(r'\d{2}(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(\d{2})', date_part)
    date_str = ""
    if d_match:
        date_str = f"{int(d_match.group(2))} {month_names[d_match.group(1)]}"

    # Parse teams — 6 chars = two 3-letter codes, e.g. BOSSAS = BOS + SAS
    context = ""
    if len(team_str) == 6:
        t1, t2 = team_str[:3], team_str[3:]
        context = f"({t1} vs {t2}"
    elif len(team_str) == 3:
        context = f"(vs {team_str}"

    if context and date_str:
        context += f" · {date_str})"
    elif context:
        context += ")"
    elif date_str:
        context = f"({date_str})"
    else:
        return title

    return f"{title} {context}"

# Micro-market title patterns that are in-game noise, not research targets
# Novelty/micro-market patterns that score 0 — not useful for research

def build_news_query(market_title, category):
    """Build a tight, specific NewsAPI query from a market title."""
    # Strip prediction market boilerplate
    stop = ["will","the","a","an","in","of","to","by","for","at","on","is","are",
            "does","do","who","what","when","how","which","be","been","has","have",
            "yes","no","over","under","more","less","than","between","or","and",
            "during","professional","basketball","game","match","season"]
    words = [w.strip("?.,!") for w in market_title.split() if w.lower().strip("?.,!") not in stop and len(w) > 2]

    # Take the most meaningful 4-5 words
    query_words = words[:5]

    # Category-specific boosters
    boosters = {
        "Politics & Macro": ["election","policy","congress","senate"],
        "Sports": ["game","stats","injury","trade"],
        "Crypto": ["price","market","regulation"],
        "Tech & Markets": ["earnings","stock","announcement"],
        "Entertainment & Legal": ["trial","verdict","release"],
    }
    # Don't add booster if already in query
    boost = [b for b in boosters.get(category, []) if b not in " ".join(query_words).lower()]
    if boost: query_words.append(boost[0])

    return " ".join(query_words)

@st.cache_data(ttl=1800)  # cache 30 min
def fetch_news(query, max_articles=5):
    """Fetch recent news articles via NewsAPI."""
    if not NEWSAPI_KEY:
        return []
    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": max_articles,
                "apiKey": NEWSAPI_KEY,
            },
            timeout=8,
        )
        data = r.json()
        articles = data.get("articles", [])
        return [
            {
                "title":       a.get("title", ""),
                "source":      a.get("source", {}).get("name", ""),
                "published":   a.get("publishedAt", "")[:10],
                "url":         a.get("url", ""),
                "description": a.get("description", "") or "",
            }
            for a in articles
            if a.get("title") and "[Removed]" not in a.get("title", "")
        ]
    except Exception:
        return []

@st.cache_data(ttl=3600)
def generate_market_research(market_title, current_price, category, edge_score, price_change_pct, news_headlines, today_date="", player_stats_summary="", sport_label=""):
    """Call Claude Sonnet to generate a sharp market research card."""
    if not ANTHROPIC_API_KEY:
        return None

    news_block = ""
    if news_headlines:
        news_block = "\n".join([
            f"- [{a['source']} {a['published']}] {a['title']}" +
            (f"\n  {a['description'][:120]}" if a.get('description') else "")
            for a in news_headlines[:5]
        ])
    else:
        news_block = "No recent news found."

    system = """You are an elite prediction market analyst. Assess whether a market is mispriced.

RULES — follow these exactly:
1. Be brutally specific. If news mentions a 3-0 scoreline, a key injury, a poll number — cite it by name.
2. If price moved >15%, something specific caused it. Find it in the headlines and name it.
3. Use hard base rates: "Teams trailing 3-0 after first leg advance ~2% historically in Champions League."
4. fair_value must be YOUR genuine estimate — not just the current price echoed back.
5. bear_case and bull_case are the realistic low/high range — typically ±8-20pp from fair_value.
6. narrative_flag = true ONLY if price moved >15% AND the headlines don't explain why.
7. reasoning must be 2-3 sentences, specific, no vague phrases like "market uncertainty" or "various factors".
8. Use today's date to calculate current player ages accurately — do NOT use ages from prior seasons.
9. If recent game stats are provided, use them as the primary form indicator over general reputation.

Return ONLY valid JSON, no markdown, no explanation:
{
  "fair_value": <0.01-0.99>,
  "bear_case": <0.01-0.99>,
  "bull_case": <0.01-0.99>,
  "verdict": "OVERPRICED" | "UNDERPRICED" | "FAIRLY PRICED",
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "reasoning": "<2-3 sharp sentences citing specific facts from the news or recent stats>",
  "key_risk": "<single most specific factor that could flip this verdict>",
  "base_rate": "<one hard historical stat, or N/A>",
  "narrative_flag": true | false,
  "narrative_flag_reason": "<one sentence if flag is true, else empty string>"
}"""

    stats_block = f"\nRecent team/player stats (use as primary form indicator):\n{player_stats_summary}" if player_stats_summary else ""
    sport_block = f"\nSport: {sport_label}" if sport_label else ""

    prompt = f"""Market: {market_title}
Current probability: {current_price:.1%}
Category: {category}{sport_block}
Edge score: {edge_score}/100
Price change: {price_change_pct:+.1f}% since tracking began
Today's date: {today_date or "March 2026"}
{stats_block}
Recent news (most recent first):
{news_block}

Assess this market now."""

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1024,
                "system": system,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30,
        )
        r.raise_for_status()
        text = r.json()["content"][0]["text"].strip()
        # Strip any accidental markdown fences
        text = text.replace("```json", "").replace("```", "").strip()
        # Find the JSON object even if there's stray text
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]
        result = json.loads(text)
        # Ensure required fields with safe defaults
        result.setdefault("fair_value", current_price)
        result.setdefault("bear_case", max(0.01, result["fair_value"] - 0.10))
        result.setdefault("bull_case", min(0.99, result["fair_value"] + 0.10))
        result.setdefault("verdict", "FAIRLY PRICED")
        result.setdefault("confidence", "LOW")
        result.setdefault("reasoning", "")
        result.setdefault("key_risk", "")
        result.setdefault("base_rate", "N/A")
        result.setdefault("narrative_flag", False)
        result.setdefault("narrative_flag_reason", "")
        return result
    except requests.exceptions.Timeout:
        return {"_error": "API request timed out (>30s). Try again."}
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        body   = e.response.text[:300] if e.response is not None else ""
        return {"_error": f"HTTP {status}: {body}"}
    except json.JSONDecodeError as e:
        return {"_error": f"JSON parse failed: {e}. Raw: {text[:300]}"}
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}"}

def _mini_table_html(entity_stats, color):
    """Render a compact last-5-games table for one player or team."""
    if not entity_stats or not entity_stats.get("games"):
        return ""
    g    = entity_stats["games"]
    name = entity_stats.get("team") or entity_stats.get("player", "")
    keys = list(g[0].keys())[:5]
    _th  = "padding:4px 8px;font-size:9px;color:#999ea6;border-bottom:1px solid #1e2530;text-align:left;letter-spacing:0.08em;text-transform:uppercase;"
    _td  = "padding:5px 8px;font-size:11px;color:#c5cad3;border-bottom:1px solid rgba(30,37,48,0.5);"
    hdrs = "".join(f"<th style='{_th}'>{h}</th>" for h in keys)
    rows = "".join(
        "<tr>" + "".join(f"<td style='{_td}'>{r.get(k,'-')}</td>" for k in keys) + "</tr>"
        for r in g
    )
    return f"""
<div style='margin-bottom:4px;'>
  <div style='font-size:10px;color:{color};font-weight:700;letter-spacing:0.08em;
    text-transform:uppercase;margin-bottom:6px;border-left:2px solid {color};
    padding-left:8px;'>{name} · last {len(g)} games</div>
  <table style='border-collapse:collapse;width:100%;'>
    <thead><tr>{hdrs}</tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""


def render_edge_breakdown(breakdown, es):
    """Render edge score breakdown as horizontal bar chart HTML."""
    max_abs = max((abs(v) for v in breakdown.values()), default=1) or 1
    bars = ""
    for label, val in breakdown.items():
        if val == 0:
            continue
        color = "#00C2A8" if val > 0 else "#DC2626"
        pct   = min(abs(val) / max_abs * 100, 100)
        sign  = f"+{val}" if val > 0 else str(val)
        bars += f"""
<div style='display:flex;align-items:center;gap:10px;margin-bottom:6px;'>
  <div style='width:120px;font-size:10px;color:#636870;text-align:right;flex-shrink:0;
    letter-spacing:0.06em;'>{label}</div>
  <div style='flex:1;background:#1c2028;height:5px;overflow:hidden;'>
    <div style='height:5px;width:{pct:.0f}%;background:{color};'></div>
  </div>
  <div style='width:32px;font-size:10px;color:{color};font-weight:700;
    text-align:right;flex-shrink:0;'>{sign}</div>
</div>"""
    return f"""
<div style='background:#0f1318;border:1px solid #1e2530;padding:14px 16px;margin:4px 0 8px 0;'>
  <div style='font-size:9px;color:#636870;letter-spacing:0.14em;text-transform:uppercase;
    margin-bottom:10px;'>// EDGE SCORE &nbsp;<span style='color:#eef2f9;font-size:13px;
    font-weight:700;'>{es}</span></div>
  {bars}
</div>"""


def render_bet_curtain(bet, sport_label):
    """Render recent form curtain (stats only — edge breakdown is separate)."""
    cp    = bet["current_price"]
    chg   = bet["price_change_pct"]
    days  = bet.get("days_to_close")
    snaps = int(bet.get("snapshot_count", 1))
    std   = bet.get("price_std", 0) or 0

    # ── Team / player recent form ─────────────────────────────────────────────
    stats     = detect_entity_and_fetch_stats(
        bet["event_ticker"], bet.get("category", "Sports"), sport_hint=sport_label
    )
    form_html = ""
    if stats:
        if stats.get("type") == "matchup":
            ha = _mini_table_html(stats.get("team_a"), "#F59E0B")
            hb = _mini_table_html(stats.get("team_b"), "#3B82F6")
            if ha or hb:
                form_html = f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:16px;'>{ha}{hb}</div>"
        elif stats.get("games"):
            color = "#8B5CF6" if stats["type"] == "player" else "#3B82F6"
            form_html = _mini_table_html(stats, color)

    # ── Market metadata strip ─────────────────────────────────────────────────
    days_str  = f"{int(days)}d" if days is not None and not (isinstance(days, float) and days != days) else "—"
    liq_lbl, liq_col = ("HIGH", "#00C2A8") if snaps >= 5 and std < 0.05 else \
                       ("MED",  "#F59E0B") if snaps >= 3 or std < 0.10 else \
                       ("LOW",  "#DC2626")
    chg_col   = "#00C2A8" if chg > 0 else "#DC2626"

    no_stats  = "<div style='font-size:11px;color:#4a5060;padding:8px 0;'>No stats available for this market</div>"

    return f"""
<div style='background:#0f1318;border:1px solid #1e2530;padding:14px 16px;margin:4px 0 8px 0;'>
  <div style='font-size:9px;color:#636870;letter-spacing:0.14em;text-transform:uppercase;
    margin-bottom:12px;'>// RECENT FORM</div>
  {form_html if form_html else no_stats}
  <div style='border-top:1px solid #1e2530;margin-top:12px;padding-top:10px;
    display:flex;gap:20px;font-size:10px;flex-wrap:wrap;color:#636870;'>
    <span>CLOSES &nbsp;<b style='color:#c5cad3;'>{days_str}</b></span>
    <span>PRICE &nbsp;<b style='color:#eef2f9;'>{cp:.0%}</b></span>
    <span>CHANGE &nbsp;<b style='color:{chg_col};'>{'+' if chg>0 else ''}{chg:.1f}%</b></span>
    <span>VOL &nbsp;<b style='color:#c5cad3;'>{std*100:.1f}%σ</b></span>
    <span>LIQ &nbsp;<b style='color:{liq_col};'>{liq_lbl}</b>&nbsp;<span style='color:#4a5060;'>({snaps} snaps)</span></span>
  </div>
</div>"""


def render_research_card(row, research, news, edge_score, df_all):
    """Render full market research card HTML."""
    cp = row["current_price"]
    verdict_colors = {"OVERPRICED": "#DC2626", "UNDERPRICED": "#00C2A8", "FAIRLY PRICED": "#F59E0B"}
    ec = edge_score_color(edge_score)

    # source link
    if row["source"] == "polymarket":
        bet_url = f"https://polymarket.com/event/{row['ticker']}"
        src_label = "🟣 Polymarket"
    else:
        bet_url = f"https://kalshi.com/markets/{row['ticker']}"
        src_label = "🔵 Kalshi"

    # verdict block
    if research:
        fv = research.get("fair_value", cp)
        verdict = research.get("verdict", "FAIRLY PRICED")
        confidence = research.get("confidence", "LOW")
        reasoning = research.get("reasoning", "")
        key_risk = research.get("key_risk", "")
        base_rate = research.get("base_rate", "N/A")
        vc = verdict_colors.get(verdict, "#888888")
        fv_diff = fv - cp
        diff_str = f"+{fv_diff:.0%}" if fv_diff >= 0 else f"{fv_diff:.0%}"
        diff_color = "#00C2A8" if fv_diff > 0.02 else "#DC2626" if fv_diff < -0.02 else "#F59E0B"

        bear = research.get("bear_case", max(0.01, fv - 0.12))
        bull = research.get("bull_case", min(0.99, fv + 0.12))
        narrative_flag = research.get("narrative_flag", False)
        narrative_reason = research.get("narrative_flag_reason", "")

        # Liquidity assessment
        snap = row.get("snapshot_count", 1)
        std  = row.get("price_std", 0)
        if snap >= 5 and std < 0.05:
            liq_label, liq_color, liq_desc = "HIGH", "#00C2A8", "Active market, tight spread"
        elif snap >= 3 or std < 0.10:
            liq_label, liq_color, liq_desc = "MEDIUM", "#F59E0B", "Moderate activity"
        else:
            liq_label, liq_color, liq_desc = "LOW", "#DC2626", "Thin market — wide spread risk"

        # Confidence band bar — visual range
        band_pct = bull - bear
        bear_left = f"{bear:.0%}"
        bull_right = f"{bull:.0%}"
        fv_pct = f"{fv:.0%}"
        # position of fair value within band as % for CSS
        band_range = max(bull - bear, 0.01)
        fv_pos = min(max((fv - bear) / band_range * 100, 5), 95)

        # Build narrative gap HTML conditionally — avoids .format() KeyError
        narrative_html = ""
        if narrative_flag:
            narrative_html = f"""<div style="background:#1A0F00;border:1px solid #F59E0B44;border-left:3px solid #F59E0B;border-radius:1px;padding:14px;margin-bottom:12px;">
  <div style="font-size:10px;color:#F59E0B;letter-spacing:0.1em;font-weight:700;text-transform:uppercase;margin-bottom:4px;">⚠️ Narrative Gap Detected</div>
  <div style="font-size:12px;color:#c5cad3;">{narrative_reason}</div>
</div>"""

        verdict_html = f"""
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px;">
  <div style="background:#14181e;border:1px solid #1e2530;border-radius:2px;padding:16px;text-align:center;">
    <div style="font-size:10px;color:#999ea6;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">Current Price</div>
    <div style="font-size:28px;font-weight:700;color:#fff;">{cp:.0%}</div>
  </div>
  <div style="background:#14181e;border:1px solid #1e2530;border-radius:2px;padding:16px;text-align:center;">
    <div style="font-size:10px;color:#999ea6;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">Fair Value</div>
    <div style="font-size:28px;font-weight:700;color:{diff_color};">{fv:.0%} <span style="font-size:14px;">({diff_str})</span></div>
  </div>
  <div style="background:#14181e;border:1px solid {vc};border-radius:2px;padding:16px;text-align:center;">
    <div style="font-size:10px;color:#999ea6;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">Verdict</div>
    <div style="font-size:18px;font-weight:700;color:{vc};">{verdict}</div>
    <div style="font-size:10px;color:#999ea6;margin-top:4px;">{confidence} confidence</div>
  </div>
</div>

<div style="background:#0f1318;border:1px solid #1e2530;border-radius:2px;padding:16px;margin-bottom:12px;">
  <div style="font-size:10px;color:#999ea6;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:10px;">📊 Confidence Band — Fair Value Range</div>
  <div style="display:flex;justify-content:space-between;font-size:11px;color:#666;margin-bottom:6px;">
    <span>Bear {bear_left}</span>
    <span style="color:#eef2f9;font-weight:600;">Fair Value {fv_pct}</span>
    <span>Bull {bull_right}</span>
  </div>
  <div style="background:#1c2028;border-radius:4px;height:8px;position:relative;overflow:hidden;">
    <div style="position:absolute;left:0;top:0;height:100%;width:100%;background:linear-gradient(90deg,#DC2626 0%,#F59E0B 50%,#00C2A8 100%);opacity:0.3;border-radius:4px;"></div>
    <div style="position:absolute;left:{fv_pos:.0f}%;top:-2px;width:3px;height:12px;background:#FFF;border-radius:2px;transform:translateX(-50%);"></div>
  </div>
  <div style="font-size:10px;color:#636870;margin-top:6px;text-align:center;">If correct, current price of {cp:.0%} is outside this range → potential edge</div>
</div>

<div style="background:#0f1318;border:1px solid #1e2530;border-left:3px solid {vc};border-radius:1px;padding:16px;margin-bottom:12px;">
  <div style="font-size:11px;color:#888;line-height:1.7;">{reasoning}</div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px;">
  <div style="background:#0f1318;border:1px solid #1e2530;border-radius:1px;padding:12px;">
    <div style="font-size:10px;color:#999ea6;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Key Risk</div>
    <div style="font-size:12px;color:#c5cad3;">{key_risk}</div>
  </div>
  <div style="background:#0f1318;border:1px solid #1e2530;border-radius:1px;padding:12px;">
    <div style="font-size:10px;color:#999ea6;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Historical Base Rate</div>
    <div style="font-size:12px;color:#c5cad3;">{base_rate}</div>
  </div>
  <div style="background:#0f1318;border:1px solid {liq_color}22;border-radius:1px;padding:12px;">
    <div style="font-size:10px;color:#999ea6;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Liquidity</div>
    <div style="font-size:13px;font-weight:700;color:{liq_color};">{liq_label}</div>
    <div style="font-size:10px;color:#999ea6;margin-top:2px;">{liq_desc}</div>
  </div>
</div>
{narrative_html}"""
    else:
        verdict_html = f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;">
  <div style="background:#14181e;border:1px solid #1e2530;border-radius:2px;padding:16px;text-align:center;">
    <div style="font-size:10px;color:#999ea6;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">Current Price</div>
    <div style="font-size:28px;font-weight:700;color:#fff;">{cp:.0%}</div>
  </div>
  <div style="background:#14181e;border:1px solid #1e2530;border-radius:2px;padding:16px;text-align:center;">
    <div style="font-size:10px;color:#999ea6;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">Edge Score</div>
    <div style="font-size:28px;font-weight:700;color:{ec};">{edge_score}</div>
  </div>
</div>"""

    # news block
    if news:
        news_items = ""
        for a in news[:4]:
            news_items += f"""<div style="padding:10px 0;border-bottom:1px solid #151515;">
  <a href="{a['url']}" target="_blank" style="font-size:13px;color:#E0E0E0;text-decoration:none;font-weight:500;line-height:1.4;">{a['title']}</a>
  <div style="font-size:10px;color:#636870;margin-top:4px;">{a['source']} · {a['published']}</div>
</div>"""
        news_html = f"""<div style="margin-bottom:16px;">
<div style="font-size:10px;color:#999ea6;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px;">📰 Recent News</div>
{news_items}
</div>"""
    else:
        news_html = '<div style="font-size:12px;color:#636870;margin-bottom:16px;">No recent news found for this market.</div>'

    card = f"""
<div style="background:#14181e;border:1px solid #1e2530;border-radius:2px;padding:24px;margin-bottom:16px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;">
    <div style="flex:1;margin-right:16px;">
      <div style="font-size:10px;color:#636870;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">{src_label} · {get_sport_label(row.get('ticker',''), row.get('event_ticker','')) or row['category']}</div>
      <div style="font-size:16px;font-weight:600;color:#eef2f9;line-height:1.4;">{row['event_ticker']}</div>
    </div>
    <div style="display:flex;align-items:center;gap:12px;flex-shrink:0;">
      <div style="text-align:center;">
        <div style="font-size:9px;color:#636870;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">EDGE</div>
        <div style="font-size:20px;font-weight:700;color:{ec};">{edge_score}</div>
        <div style="font-size:9px;color:{ec};letter-spacing:0.06em;">{edge_score_label(edge_score)}</div>
      </div>
      <a href="{bet_url}" target="_blank" style="border:1px solid {_RED};color:{_RED};font-size:10px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;padding:8px 18px;border-radius:1px;text-decoration:none;">BET →</a>
    </div>
  </div>
  {verdict_html}
  {news_html}
</div>"""
    return card

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — MARKET RESEARCH TERMINAL
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("## 🔍 Market Research Terminal")
    st.markdown(
        "<div style='color:#999ea6;font-size:14px;margin-bottom:28px;'>Search any topic. We surface live markets, score each edge opportunity, pull recent news, and give you a verdict.</div>",
        unsafe_allow_html=True,
    )

    # ── search + filters ──────────────────────────────────────────────────────
    sr1, sr2, sr3 = st.columns([3, 1, 1])
    with sr1:
        search_query = st.text_input("Search markets", placeholder="Search markets — e.g. 'LeBron', 'Trump', 'Bitcoin ETF', 'Lakers'...", key="research_query", label_visibility="collapsed")
    with sr2:
        research_cat = st.selectbox("Category", ["All"] + sorted(df_markets["category"].unique().tolist()), key="res_cat", label_visibility="collapsed")
    with sr3:
        research_src = st.selectbox("Source", ["All", "Polymarket", "Kalshi"], key="res_src", label_visibility="collapsed")

    # ── filter markets ────────────────────────────────────────────────────────
    df_res = df_markets.copy()
    # Filter out markets that have already closed
    now_utc = pd.Timestamp.now(tz="UTC")
    df_res = df_res[
        pd.to_datetime(df_res["close_time"], errors="coerce", utc=True).isna() |
        (pd.to_datetime(df_res["close_time"], errors="coerce", utc=True) > now_utc)
    ]
    if research_cat != "All":
        df_res = df_res[df_res["category"] == research_cat]
    if research_src == "Polymarket":
        df_res = df_res[df_res["source"] == "polymarket"]
    elif research_src == "Kalshi":
        df_res = df_res[df_res["source"] == "kalshi"]

    if search_query.strip():
        # Strip common noise words that appear in almost every market title
        _search_stop = {"vs","the","a","an","in","of","to","by","for","at","on","is","are",
                        "will","who","what","when","how","does","do","be","and","or","that",
                        "if","its","with","from","this","has","had","have","more","than","over",
                        "under","per","get","got","make","made","new","next","last","top"}
        # Team nickname → precise title patterns used in Kalshi/Polymarket event titles.
        # LA teams use the Kalshi suffix (L = Lakers, C = Clippers) to avoid cross-sport matches.
        _TEAM_ALIASES = {
            "celtics": ["boston"], "knicks": ["new york"], "nets": ["brooklyn"],
            "raptors": ["toronto"], "sixers": ["philadelphia"], "76ers": ["philadelphia"],
            "bulls": ["chicago"], "cavaliers": ["cleveland"], "cavs": ["cleveland"],
            "pistons": ["detroit"], "pacers": ["indiana"], "bucks": ["milwaukee"],
            "hawks": ["atlanta"], "hornets": ["charlotte"], "heat": ["miami"],
            "magic": ["orlando"], "wizards": ["washington"],
            "nuggets": ["denver"], "timberwolves": ["minnesota"], "wolves": ["minnesota"],
            "thunder": ["oklahoma"], "trailblazers": ["portland"], "blazers": ["portland"],
            "jazz": ["utah"], "warriors": ["golden state"],
            # LA teams — use team-specific suffix so NHL Kings / other LA teams don't match
            "lakers":   ["los angeles l"],   # Kalshi: "Los Angeles L at Indiana"
            "clippers": ["los angeles c"],   # Kalshi: "Toronto at Los Angeles C"
            "suns": ["phoenix"], "kings": ["sacramento"],
            "mavericks": ["dallas"], "mavs": ["dallas"],
            "rockets": ["houston"], "grizzlies": ["memphis"],
            "pelicans": ["new orleans"], "spurs": ["san antonio"],
        }
        # Kalshi ticker team codes for futures markets (e.g. KXNBA-26-LAL)
        # where the title says "Will the Los Angeles win..." without L/C suffix
        _TICKER_CODES = {
            "lakers": ["LAL"], "clippers": ["LAC"], "celtics": ["BOS"],
            "knicks": ["NYK"], "nets": ["BKN"], "raptors": ["TOR"],
            "sixers": ["PHI"], "76ers": ["PHI"], "bulls": ["CHI"],
            "cavaliers": ["CLE"], "cavs": ["CLE"], "pistons": ["DET"],
            "pacers": ["IND"], "bucks": ["MIL"], "hawks": ["ATL"],
            "hornets": ["CHA"], "heat": ["MIA"], "magic": ["ORL"],
            "wizards": ["WAS"], "nuggets": ["DEN"], "timberwolves": ["MIN"],
            "wolves": ["MIN"], "thunder": ["OKC"], "trailblazers": ["POR"],
            "blazers": ["POR"], "jazz": ["UTA"], "warriors": ["GSW"],
            "lakers": ["LAL"], "clippers": ["LAC"], "suns": ["PHX"],
            "kings": ["SAC"], "mavericks": ["DAL"], "mavs": ["DAL"],
            "rockets": ["HOU"], "grizzlies": ["MEM"], "pelicans": ["NOP"],
            "spurs": ["SAS"],
        }
        _NBA_TEAMS    = set(_TEAM_ALIASES.keys())
        _NHL_KEYWORDS = {"nhl", "stanley cup", "hockey", "ice hockey"}
        _NHL_TEAMS    = {"kings", "ducks", "sharks", "kings", "coyotes", "flames",
                         "oilers", "canucks", "golden knights", "kraken", "wild",
                         "blackhawks", "red wings", "blue jackets", "predators",
                         "blues", "avalanche", "stars", "jets", "canadiens",
                         "senators", "maple leafs", "bruins", "sabres", "rangers",
                         "islanders", "devils", "flyers", "penguins", "capitals",
                         "hurricanes", "panthers", "lightning", "thrashers"}

        def _term_matches(title, term, ticker=""):
            # Hard exclusion: NBA team searches must not return NHL markets
            if term in _NBA_TEAMS and any(kw in title for kw in _NHL_KEYWORDS):
                return False
            if term in _TEAM_ALIASES:
                if term in title:
                    return True
                if any(a in title for a in _TEAM_ALIASES[term]):
                    return True
                # Also check Kalshi ticker team codes for futures (title may just say city)
                if term in _TICKER_CODES:
                    t_up = ticker.upper()
                    if any(code in t_up for code in _TICKER_CODES[term]):
                        return True
                return False
            return term in title

        terms = [t for t in search_query.lower().split() if len(t) > 1 and t not in _search_stop]
        if not terms:
            terms = [t for t in search_query.lower().split() if len(t) > 1]  # fallback if all stripped

        # AND logic — all meaningful terms must appear in the market title or ticker (alias-aware)
        mask = df_res.apply(
            lambda row: all(_term_matches(row["event_ticker"].lower(), term, row.get("ticker", "")) for term in terms),
            axis=1
        )
        df_res = df_res[mask]

        # Fallback: if AND returns nothing AND we have 2+ terms, relax but require at least
        # ceil(n/2) terms to match — avoids dumping in loosely related markets
        if df_res.empty and len(terms) > 1:
            min_matches = max(2, -(-len(terms) // 2))  # ceil(n/2), minimum 2
            df_res_base = df_markets.copy()
            now_utc2 = pd.Timestamp.now(tz="UTC")
            df_res_base = df_res_base[
                pd.to_datetime(df_res_base["close_time"], errors="coerce", utc=True).isna() |
                (pd.to_datetime(df_res_base["close_time"], errors="coerce", utc=True) > now_utc2)
            ]
            if research_cat != "All":
                df_res_base = df_res_base[df_res_base["category"] == research_cat]
            if research_src == "Polymarket":
                df_res_base = df_res_base[df_res_base["source"] == "polymarket"]
            elif research_src == "Kalshi":
                df_res_base = df_res_base[df_res_base["source"] == "kalshi"]
            mask_partial = df_res_base.apply(
                lambda row: sum(1 for term in terms if _term_matches(row["event_ticker"].lower(), term, row.get("ticker", ""))) >= min_matches,
                axis=1
            )
            df_res = df_res_base[mask_partial]
            if not df_res.empty:
                st.caption(f"No exact matches — showing markets containing at least {min_matches} of: {', '.join(terms)}")

    # ── compute edge scores ───────────────────────────────────────────────────
    if not df_res.empty:
        df_res = df_res.copy()
        _cat_avg = df_markets.groupby("category")["price_change_pct"].mean().to_dict()
        df_res["edge_score"] = df_res.apply(lambda r: compute_edge_score(r, _cat_avg), axis=1)
        df_res["_sort_days"] = df_res["days_to_close"].fillna(9999)
        df_res = df_res.sort_values(["_sort_days", "edge_score"], ascending=[True, False]).reset_index(drop=True)
        # Pre-compute game_key and market_type so the display loop can use them
        # (functions defined inside the tab block below, after df_res is built)
        # Collapse mention markets only — keep 1 per game, preserve all other outcomes
        _gk_tmp = df_res["ticker"].str.upper().str.extract(
            r'(\d{2}(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\d{2}[A-Z]{6})'
        )[0].fillna(df_res["event_ticker"])
        _is_mention = df_res["ticker"].str.upper().str.startswith(("KXNBAMENTION","KXNCAABMENTION"))
        df_res = pd.concat([
            df_res[~_is_mention],
            df_res[_is_mention].assign(_gk=_gk_tmp[_is_mention]).drop_duplicates(subset=["_gk"], keep="first").drop(columns=["_gk"], errors="ignore")
        ]).sort_values(["_sort_days", "edge_score"], ascending=[True, False]).reset_index(drop=True)

    # ── summary bar ───────────────────────────────────────────────────────────
    if not df_res.empty:
        sb1, sb2, sb3, sb4 = st.columns(4)
        sb1.metric("Markets found", len(df_res))
        sb2.metric("Avg Edge Score", f"{df_res['edge_score'].mean():.0f}/100")
        sb3.metric("Strong edges (75+)", len(df_res[df_res["edge_score"] >= 75]))
        sb4.metric("Avg probability", f"{df_res['current_price'].mean():.0%}")

        st.markdown("---")

        # ── group markets by event (shared event_ticker prefix) ───────────────
        # Extract event group: strip the last "option" token if title contains "?"
        # e.g. "Boston at Oklahoma City Winner?" → group key "Boston at Oklahoma City"
        # For non-search (browse mode), fall back to flat table
        def extract_event_group(title):
            """Strip the outcome token to get the parent event name."""
            import re
            t = title.strip()
            # Remove trailing "?" and common outcome suffixes
            t = re.sub(r'\?\s*$', '', t).strip()
            # If title has a parenthetical context like (BOS vs OKC · 12 Mar), keep it but don't group on it
            t = re.sub(r'\s*\(.*?\)\s*$', '', t).strip()
            # Remove outcome tokens at the end: "Winner", "to win", "by X-Y", "set score", "spread"
            t = re.sub(r'\b(winner|to win|wins|spread|moneyline|total|over|under|by \d[\d-]*)\s*$', '', t, flags=re.IGNORECASE).strip()
            return t if t else title

        def extract_game_key(ticker, event_ticker):
            """Extract a stable game identifier from Kalshi tickers (e.g. '26MAR10CHAPOR').
            Falls back to extract_event_group(event_ticker) for Polymarket / non-game tickers."""
            import re as _re2
            if ticker and isinstance(ticker, str):
                m = _re2.search(
                    r'(\d{2}(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\d{2})([A-Z]{6})',
                    ticker.upper()
                )
                if m:
                    return m.group(0)
            return extract_event_group(event_ticker)

        def get_market_type(ticker):
            """Map Kalshi ticker prefix to a human-readable market type."""
            if not ticker or not isinstance(ticker, str):
                return "Market"
            t = ticker.upper()
            if any(t.startswith(p) for p in ["KXNBAGAME","KXNCAABBGAME","KXNCAAWBGAME","KXNHLGAME","KXMLSGAME",
                                               "KXMLBGAME","KXUCLGAME","KXEPLGAME","KXNCAABGAME"]):
                return "Game Winner"
            if any(t.startswith(p) for p in ["KXNBASPREAD","KXNBA1HSPREAD","KXNBA2HSPREAD"]):
                return "Spread"
            if any(t.startswith(p) for p in ["KXNBATOTAL","KXNBA1HTOTAL","KXNBA2HTOTAL"]):
                return "Total Points"
            if any(t.startswith(p) for p in ["KXNBA1HWINNER","KXNBA2HWINNER"]):
                return "Half Winner"
            if any(t.startswith(p) for p in ["KXNBA2D","KXNBA3D"]):
                return "Lead After Q"
            if any(t.startswith(p) for p in ["KXNBAPTS","KXNBAREB","KXNBAAST","KXNBA3PT","KXNBABLK","KXNBASTL",
                                               "KXNHLPTS","KXNHLAST","KXNHLGOAL"]):
                return "Player Prop"
            if any(t.startswith(p) for p in ["KXNBAMENTION","KXNCAABMENTION"]):
                return "Mention"
            if any(t.startswith(p) for p in ["KXATPMATCH","KXWTAMATCH","KXATPSETWINNER","KXWTASETWINNER",
                                               "KXCS2GAME","KXCS2MAP"]):
                return "Match Winner"
            if t.startswith("KXEPLGOAL"):
                return "Goal Market"
            return "Market"

        _MONTH_NUM = {"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,
                      "JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}
        def parse_game_date(game_key):
            """Parse actual game date from Kalshi game_key (e.g. '26MAR25LALIND' → 2026-03-25).
            Kalshi NBA markets close ~14 days after game day, so close_time ≠ game date."""
            import re as _re3
            m = _re3.match(
                r'(\d{2})(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)(\d{2})',
                str(game_key)
            )
            if m:
                return pd.Timestamp(year=2000+int(m.group(1)),
                                    month=_MONTH_NUM[m.group(2)],
                                    day=int(m.group(3)))
            return pd.NaT

        # When searching, show all matching markets across the full 14-day window.
        # When browsing (no query), cap at 300 to avoid rendering thousands of expanders.
        near_term = df_res[df_res["days_to_close"].between(0, 7, inclusive="both")]
        the_rest   = df_res[~df_res.index.isin(near_term.index)]
        _cap = 1000 if search_query.strip() else 300
        display_df = pd.concat([near_term, the_rest]).head(_cap).copy()
        _closes_dt = pd.to_datetime(display_df["close_time"], errors="coerce", utc=True)
        display_df["Closes"] = _closes_dt.dt.strftime("%d %b").str.lstrip("0").replace("", "—")
        display_df["enriched_title"] = display_df.apply(
            lambda r: enrich_title_with_context(r["event_ticker"], r["ticker"], r.get("close_time", "")), axis=1
        )
        display_df["game_key"] = display_df.apply(
            lambda r: extract_game_key(r["ticker"], r["event_ticker"]), axis=1
        )
        display_df["market_type"] = display_df["ticker"].apply(get_market_type)

        # When searching, enrich each matched game card with ALL related markets
        # (props, spreads, totals) even if their titles didn't match the search query.
        if search_query.strip():
            _all_gk = df_markets.copy()
            _all_gk["game_key"] = _all_gk.apply(
                lambda r: extract_game_key(r["ticker"], r["event_ticker"]), axis=1
            )
            _matched_keys = set(display_df["game_key"].unique())
            _related = _all_gk[_all_gk["game_key"].isin(_matched_keys)]
            _new_rows = _related[~_related["ticker"].isin(set(display_df["ticker"]))].copy()
            if not _new_rows.empty:
                _new_rows["edge_score"] = _new_rows.apply(lambda r: compute_edge_score(r, _cat_avg), axis=1)
                _ndt = pd.to_datetime(_new_rows["close_time"], errors="coerce", utc=True)
                _new_rows["Closes"] = _ndt.dt.strftime("%d %b").str.lstrip("0").replace("", "—")
                _new_rows["enriched_title"] = _new_rows.apply(
                    lambda r: enrich_title_with_context(r["event_ticker"], r["ticker"], r.get("close_time", "")), axis=1
                )
                _new_rows["market_type"] = _new_rows["ticker"].apply(get_market_type)
                display_df = pd.concat([display_df, _new_rows], ignore_index=True)

        # ── Unified game card + expander view ─────────────────────────────────
        # Maps Kalshi outcome code (ticker suffix) → display name for game winner rows
        _OUTCOME_NAMES = {
            # NBA
            "LAL":"Los Angeles L","LAC":"Los Angeles C","BKN":"Brooklyn","NYK":"New York",
            "BOS":"Boston","PHI":"Philadelphia","TOR":"Toronto","MIA":"Miami","ORL":"Orlando",
            "ATL":"Atlanta","CHA":"Charlotte","WAS":"Washington","CHI":"Chicago","CLE":"Cleveland",
            "DET":"Detroit","IND":"Indiana","MIL":"Milwaukee","MEM":"Memphis","NOP":"New Orleans",
            "SAS":"San Antonio","HOU":"Houston","DAL":"Dallas","OKC":"Oklahoma City","DEN":"Denver",
            "MIN":"Minnesota","UTA":"Utah","POR":"Portland","SAC":"Sacramento","PHX":"Phoenix",
            "GSW":"Golden State",
            # MLB
            "LAD":"Los Angeles D","LAA":"Los Angeles A","NYY":"New York Y","NYM":"New York M",
            "CHC":"Chicago C","CWS":"Chicago W","STL":"St. Louis","MIL":"Milwaukee",
            "CIN":"Cincinnati","PIT":"Pittsburgh","SFG":"San Francisco","COL":"Colorado",
            "ARI":"Arizona","AZ":"Arizona","SDN":"San Diego","HOU":"Houston","ATL":"Atlanta",
            "MIA":"Miami","NYM":"New York M","PHI":"Philadelphia","WSN":"Washington",
            "MIN":"Minnesota","CLE":"Cleveland","DET":"Detroit","KCR":"Kansas City",
            "TBR":"Tampa Bay","BAL":"Baltimore","BOS":"Boston","TOR":"Toronto","TEX":"Texas",
            "SEA":"Seattle","OAK":"Oakland",
            # NHL
            "LAK":"Los Angeles K","ANA":"Anaheim","SJS":"San Jose",
            # Soccer
            "TIE":"Draw",
        }

        _TYPE_ORDER = ["Game Winner", "Match Winner", "Spread", "Total Points", "Half Winner",
                       "Lead After Q", "Goal Market", "Player Prop", "Market", "Mention"]

        game_meta = (
            display_df.groupby("game_key", sort=False)
            .agg(
                min_days=("days_to_close", "min"),
                best_edge=("edge_score", "max"),
                closes=("Closes", "first"),
                n_markets=("ticker", "count"),
            )
        )
        # Parse actual game dates (Kalshi NBA markets close ~14 days after game day)
        _today_norm = pd.Timestamp.now().normalize()
        game_meta["game_date"]   = game_meta.index.map(parse_game_date)
        game_meta["days_to_game"] = (game_meta["game_date"] - _today_norm).dt.days
        # Sort by game/event date first, fall back to market close date, then edge score
        game_meta["_sort_key"] = game_meta["days_to_game"].where(
            game_meta["days_to_game"].notna(), game_meta["min_days"]
        ).fillna(9999)
        game_meta = game_meta.sort_values(["_sort_key", "best_edge"], ascending=[True, False])

        # Split into upcoming (game ≤14 days or close ≤14 days) vs long-term
        _days_ref = game_meta["days_to_game"].where(
            game_meta["days_to_game"].notna(), game_meta["min_days"]
        )
        _upcoming_keys = game_meta[_days_ref.notna() & (_days_ref <= 14)].index
        _futures_keys  = game_meta[~game_meta.index.isin(_upcoming_keys)].index

        def _render_game_cards(keys):
            for game_key in keys:
                meta = game_meta.loc[game_key]
                grp = display_df[display_df["game_key"] == game_key]

                # Representative title: prefer a game/match winner row
                winner_rows = grp[grp["market_type"].isin(["Game Winner", "Match Winner"])]
                game_title = (winner_rows.iloc[0]["event_ticker"] if not winner_rows.empty
                              else grp.iloc[0]["enriched_title"])

                best_edge    = int(meta["best_edge"])
                min_days     = meta["min_days"]
                days_to_game = meta["days_to_game"]
                game_date    = meta["game_date"]
                n_markets    = int(meta["n_markets"])
                closes       = meta["closes"]
                src_icons    = " ".join(grp["source"].map({"polymarket": "🟣", "kalshi": "🔵"}).dropna().unique())

                # Use game date for urgency when available (Kalshi close_time is ~14d after game)
                if pd.notna(days_to_game):
                    badge     = (" 🟢 TONIGHT" if days_to_game <= 0
                                 else " 🟡 TOMORROW" if days_to_game == 1
                                 else " 🟡 THIS WEEK" if days_to_game <= 6
                                 else "")
                    auto_open = days_to_game <= 1
                    _gd_str   = f"{int(game_date.day)} {game_date.strftime('%b')}"
                    date_chip = f"🗓 {_gd_str}"
                else:
                    badge     = (" 🟢 TODAY" if pd.notna(min_days) and min_days <= 0
                                 else " 🟡 THIS WEEK" if pd.notna(min_days) and min_days <= 3
                                 else "")
                    auto_open = pd.notna(min_days) and min_days <= 1
                    date_chip = closes

                types_in_grp = [t for t in _TYPE_ORDER if t in grp["market_type"].values]
                type_chips = "  ".join(
                    f'<span style="background:#1c2028;color:#777;font-size:9px;padding:2px 6px;border-radius:3px;">{t}</span>'
                    for t in types_in_grp
                )

                _sport_lbl  = get_sport_label(grp.iloc[0]["ticker"], grp.iloc[0]["event_ticker"]) if not grp.empty else ""
                _sport_pfx  = f"[{_sport_lbl}]  " if _sport_lbl else ""
                exp_label = f"{_sport_pfx}{game_title}{badge}  ·  {date_chip}  ·  {n_markets} market{'s' if n_markets != 1 else ''}"

                with st.expander(exp_label, expanded=auto_open):
                    st.markdown(
                        f'<div style="margin-bottom:10px;font-size:11px;color:#999ea6;">'
                        f'{src_icons} &nbsp; {type_chips}</div>',
                        unsafe_allow_html=True
                    )
                    for mtype in _TYPE_ORDER:
                        type_rows = grp[grp["market_type"] == mtype].sort_values("edge_score", ascending=False)
                        if type_rows.empty:
                            continue
                        st.markdown(
                            f'<div style="font-size:9px;color:#636870;letter-spacing:0.1em;text-transform:uppercase;'
                            f'padding:8px 0 4px;">{mtype}</div>',
                            unsafe_allow_html=True
                        )
                        for _, bet in type_rows.iterrows():
                            cp        = bet["current_price"]
                            chg       = bet["price_change_pct"]
                            es        = int(bet["edge_score"])
                            bec       = edge_score_color(es)
                            chg_color = "#00C2A8" if chg > 0 else "#DC2626"
                            chg_str   = f"+{chg:.1f}%" if chg > 0 else f"{chg:.1f}%"
                            # For game/match winners show the outcome team, not the generic title
                            if mtype in ("Game Winner", "Match Winner"):
                                _suffix = str(bet["ticker"]).rsplit("-", 1)[-1].upper()
                                _oname  = _OUTCOME_NAMES.get(_suffix, _suffix)
                                title_txt = f"{_oname} wins" if _oname != _suffix else bet["event_ticker"]
                            else:
                                title_txt = bet["event_ticker"]
                            src       = bet["source"]
                            bet_url   = (
                                f"https://polymarket.com/event/{bet['ticker']}"
                                if src == "polymarket"
                                else f"https://kalshi.com/markets/{str(bet['ticker']).split('-')[0].lower()}"
                            )
                            _rc = st.columns([5, 1, 1, 1, 1, 1, 1, 1])
                            _rc[0].markdown(
                                f'<div style="font-size:13px;color:#c5cad3;padding:4px 0;">{title_txt}</div>',
                                unsafe_allow_html=True
                            )
                            _rc[1].markdown(
                                f'<div style="font-size:13px;color:#eef2f9;font-weight:600;padding:4px 0;">{cp:.0%}</div>',
                                unsafe_allow_html=True
                            )
                            _rc[2].markdown(
                                f'<div style="font-size:12px;color:{chg_color};padding:4px 0;">{chg_str}</div>',
                                unsafe_allow_html=True
                            )
                            _bd  = compute_edge_score_breakdown(bet, _cat_avg)
                            _ed_key = f"ed_{bet['ticker']}"
                            _sc_key = f"sc_{bet['ticker']}"
                            if _rc[3].button(
                                f"{es}", key=f"edbtn_{bet['ticker']}",
                                help="Edge score breakdown"
                            ):
                                st.session_state[_ed_key] = not st.session_state.get(_ed_key, False)
                            _rc[4].markdown(
                                f'<a href="{bet_url}" target="_blank" style="font-size:9px;border:1px solid {_RED};'
                                f'color:{_RED};padding:4px 8px;border-radius:1px;font-weight:700;letter-spacing:0.1em;'
                                f'text-transform:uppercase;text-decoration:none;display:inline-block;margin-top:2px;'
                                f'transition:all 0.15s ease;">BET →</a>',
                                unsafe_allow_html=True
                            )
                            if _rc[5].button("📊", key=f"scbtn_{bet['ticker']}", help="Recent form"):
                                st.session_state[_sc_key] = not st.session_state.get(_sc_key, False)
                            if _rc[6].button("🔬", key=f"dr_{bet['ticker']}", help="Deep research"):
                                st.session_state["dr_ticker"] = bet["ticker"]
                                st.session_state.pop("dr_ticker_result", None)
                            # Edge breakdown dropdown
                            if st.session_state.get(_ed_key):
                                st.markdown(render_edge_breakdown(_bd, es), unsafe_allow_html=True)
                            # Stats curtain (form only)
                            if st.session_state.get(_sc_key):
                                st.markdown(
                                    render_bet_curtain(bet, _sport_lbl),
                                    unsafe_allow_html=True
                                )
                            # Render research card inline if this row's research is ready
                            if st.session_state.get("dr_ticker_result") == bet["ticker"] and "research_card" in st.session_state:
                                st.markdown(st.session_state["research_card"], unsafe_allow_html=True)
                                if st.session_state.get("research_sports"):
                                    st.markdown(st.session_state["research_sports"], unsafe_allow_html=True)
                                if st.button("✕ Clear", key=f"clear_dr_{bet['ticker']}"):
                                    for _k in ("research_card", "research_sports", "dr_ticker_result"):
                                        st.session_state.pop(_k, None)

        if _upcoming_keys.any():
            st.markdown("### 📅 Upcoming Games")
            st.caption("Game-specific markets closing within 14 days.")
            _render_game_cards(_upcoming_keys)

        if _futures_keys.any():
            st.markdown("### 📊 Season & Futures")
            st.caption("Long-term markets, season totals, and futures.")
            _render_game_cards(_futures_keys)

        # ── Inline deep research (triggered by per-row 🔬 buttons) ──────────────
        if st.session_state.get("dr_ticker"):
            _dr_ticker = st.session_state["dr_ticker"]
            _dr_match  = df_res[df_res["ticker"] == _dr_ticker]
            if not _dr_match.empty:
                _dr_row  = _dr_match.iloc[0]
                _dr_edge = int(_dr_row["edge_score"])
                st.markdown("---")
                st.markdown(f"### 🔬 Deep Research: {_dr_row['event_ticker']}")
                with st.spinner("Fetching news and generating analysis..."):
                    _dr_sport_lbl = get_sport_label(_dr_row.get("ticker",""), _dr_row["event_ticker"])
                    _dr_news_q    = build_news_query(_dr_row["event_ticker"], _dr_row["category"])
                    _dr_news      = fetch_news(_dr_news_q, max_articles=5)
                    _dr_stats     = detect_entity_and_fetch_stats(
                        _dr_row["event_ticker"], _dr_row["category"], sport_hint=_dr_sport_lbl
                    )
                    _dr_st_txt = ""
                    if _dr_stats:
                        if _dr_stats.get("type") == "matchup":
                            _parts = []
                            for _side_key in ("team_a", "team_b"):
                                _side = _dr_stats.get(_side_key)
                                if _side and _side.get("games"):
                                    _g = _side["games"]
                                    _parts.append(
                                        f"{_side['team']} last {len(_g)} games: " +
                                        ", ".join([f"{x['Date']}: {x.get('Score','?')} ({x.get('W/L','?')})" for x in _g])
                                    )
                            _dr_st_txt = " | ".join(_parts)
                        elif _dr_stats.get("games"):
                            _g = _dr_stats["games"]
                            if _dr_stats["type"] == "player":
                                _dr_st_txt = (f"{_dr_stats['player']} ({_dr_stats.get('team','')}) last {len(_g)} games: " +
                                              ", ".join([f"{x['Date']}: {x['PTS']}pts/{x['REB']}reb/{x['AST']}ast" for x in _g]))
                            else:
                                _dr_st_txt = (f"{_dr_stats['team']} last {len(_g)} games: " +
                                              ", ".join([f"{x['Date']}: {x.get('Score','?')} ({x.get('W/L','?')})" for x in _g]))
                    import datetime as _dt2
                    _dr_research = generate_market_research(
                        market_title=_dr_row["event_ticker"], current_price=_dr_row["current_price"],
                        category=_dr_row["category"], edge_score=_dr_edge,
                        price_change_pct=_dr_row["price_change_pct"], news_headlines=_dr_news,
                        today_date=_dt2.date.today().strftime("%B %d, %Y"),
                        player_stats_summary=_dr_st_txt,
                        sport_label=_dr_sport_lbl,
                    )
                if _dr_research and _dr_research.get("_error"):
                    st.error(f"⚠️ AI verdict failed: {_dr_research['_error']}")
                    _dr_research = None
                st.session_state["research_card"]    = render_research_card(_dr_row, _dr_research, _dr_news, _dr_edge, df_markets)
                st.session_state["research_sports"]  = render_stats_card(_dr_stats) if _dr_stats else ""
                st.session_state["dr_ticker_result"] = _dr_ticker
            st.session_state["dr_ticker"] = None
            st.rerun()

        st.caption("Click 🔬 Research on any bet row above to run AI analysis inline.")

    else:
        if search_query.strip():
            st.info(f"No markets found for '{search_query}'. Try a broader term.")
        else:
            st.info("Enter a search term above to find markets, or browse by category.")

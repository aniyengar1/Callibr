import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from supabase import create_client

st.set_page_config(page_title="QuantMarkets", page_icon="📈", layout="wide")

# ── custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background-color: #1C1C1E; }

[data-testid="stSidebar"] {
    background-color: #161618;
    border-right: 1px solid #2A2A2C;
}
[data-testid="stSidebar"] * { color: #E0E0E0 !important; }
[data-testid="stSidebar"] .stMetric {
    background: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
}

.stTabs [data-baseweb="tab-list"] {
    background-color: transparent;
    border-bottom: 1px solid #1E1E1E;
    gap: 0; padding: 0;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    color: #555555;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 12px 24px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    transition: all 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover { color: #FFFFFF; }
.stTabs [aria-selected="true"] {
    background-color: transparent !important;
    color: #FFFFFF !important;
    border-bottom: 2px solid #FFFFFF !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 32px; }

[data-testid="stMetric"] {
    background: #111111;
    border: 1px solid #1E1E1E;
    border-radius: 10px;
    padding: 20px 24px;
    transition: border-color 0.2s ease;
}
[data-testid="stMetric"]:hover { border-color: #333333; }
[data-testid="stMetricLabel"] {
    color: #555555 !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-size: 26px !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
}

h1, h2, h3, h4 {
    color: #FFFFFF !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
}
h2 { border-bottom: 1px solid #1A1A1A; padding-bottom: 12px; }

.stButton > button {
    background-color: #FFFFFF;
    color: #000000;
    border: none;
    border-radius: 6px;
    padding: 10px 28px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background-color: #E8E8E8;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(255,255,255,0.08);
}

.stSelectbox > div > div,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background-color: #111111 !important;
    border: 1px solid #222222 !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
    font-size: 13px !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid #1A1A1A;
    border-radius: 10px;
    overflow: hidden;
}

.stInfo {
    background-color: #111111 !important;
    border: 1px solid #222222 !important;
    border-left: 3px solid #FFFFFF !important;
    border-radius: 8px !important;
}
.stWarning { border-left: 3px solid #F59E0B !important; }
.stError   { border-left: 3px solid #DC2626 !important; }

.stRadio > div > label {
    background: #111111;
    border: 1px solid #222222;
    border-radius: 6px;
    padding: 8px 16px;
    color: #AAAAAA !important;
    font-size: 12px;
    transition: all 0.15s ease;
}
.stRadio > div > label:hover {
    border-color: #444444;
    color: #FFFFFF !important;
}

hr { border: none; border-top: 1px solid #1A1A1A; margin: 28px 0; }

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0A0A0A; }
::-webkit-scrollbar-thumb { background: #2A2A2A; border-radius: 2px; }

table { width: 100%; border-collapse: collapse; font-size: 13px; }
table th {
    background: #111111; color: #555555;
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.08em; text-transform: uppercase;
    padding: 12px 16px; border-bottom: 1px solid #1E1E1E; text-align: left;
}
table td { padding: 12px 16px; border-bottom: 1px solid #151515; color: #CCCCCC; }
table tr:hover td { background: #111111; }
table a {
    color: #FFFFFF; text-decoration: none; font-weight: 600;
    border-bottom: 1px solid #333333; padding-bottom: 1px;
    transition: border-color 0.15s ease;
}
table a:hover { border-bottom-color: #FFFFFF; }
</style>
""", unsafe_allow_html=True)

# ── page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:40px 0 28px 0; border-bottom:1px solid #1A1A1A; margin-bottom:32px;">
    <div style="font-size:10px;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;color:#444444;margin-bottom:10px;">PREDICTION MARKETS</div>
    <div style="font-size:38px;font-weight:700;color:#FFFFFF;letter-spacing:-0.03em;line-height:1;">QuantMarkets</div>
    <div style="font-size:14px;color:#444444;margin-top:10px;font-weight:400;letter-spacing:0.01em;">Backtest strategies · Find edges · Place smarter bets</div>
</div>
""", unsafe_allow_html=True)

# ── constants ─────────────────────────────────────────────────────────────────
SUPABASE_URL      = st.secrets["SUPABASE_URL"]
SUPABASE_KEY      = st.secrets["SUPABASE_KEY"]
ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")

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
    paper_bgcolor="#1C1C1E",
    plot_bgcolor="#1C1C1E",
    font=dict(family="Inter", color="#888888", size=11),
    margin=dict(l=16, r=16, t=36, b=16),
    xaxis=dict(gridcolor="#1A1A1A", linecolor="#222222", tickfont=dict(size=10)),
    yaxis=dict(gridcolor="#1A1A1A", linecolor="#222222", tickfont=dict(size=10)),
    hoverlabel=dict(
        bgcolor="#1A1A1A",
        bordercolor="#333333",
        font=dict(family="Inter", size=12, color="#FFFFFF"),
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
    all_rows, offset, batch_size = [], 0, 1000
    while True:
        batch = supabase.table("market_prices").select("*")\
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
    df_m["days_to_close"]    = (
        pd.to_datetime(df_m["close_time"], errors="coerce").dt.tz_localize(None) - pd.Timestamp.now()
    ).dt.days
    return df_m

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

def fetch_espn_team_stats(team_name, sport="nba"):
    """Fetch recent team stats via ESPN unofficial endpoint."""
    try:
        sport_map = {
            "nba": ("basketball", "nba"),
            "nfl": ("football", "nfl"),
            "mlb": ("baseball", "mlb"),
            "nhl": ("hockey", "nhl"),
            "soccer": ("soccer", "usa.1"),
        }
        s, league = sport_map.get(sport, ("basketball","nba"))
        r = requests.get(
            f"https://site.api.espn.com/apis/site/v2/sports/{s}/{league}/teams?limit=100",
            timeout=8
        ).json()
        teams = r.get("sports",[{}])[0].get("leagues",[{}])[0].get("teams",[])
        match = next((t["team"] for t in teams if team_name.lower() in t["team"]["displayName"].lower()), None)
        if not match: return None
        tid = match["id"]
        # Get team schedule/results
        sched = requests.get(
            f"https://site.api.espn.com/apis/site/v2/sports/{s}/{league}/teams/{tid}/schedule",
            timeout=8
        ).json()
        events = sched.get("events", [])[-5:]
        rows = []
        for e in events:
            comp = e.get("competitions",[{}])[0]
            comps = comp.get("competitors",[])
            home = next((c for c in comps if c.get("homeAway")=="home"), {})
            away = next((c for c in comps if c.get("homeAway")=="away"), {})
            rows.append({
                "Date":   e.get("date","")[:10],
                "Home":   home.get("team",{}).get("abbreviation","?"),
                "Away":   away.get("team",{}).get("abbreviation","?"),
                "Score":  f"{home.get('score','?')}-{away.get('score','?')}",
                "Result": comp.get("status",{}).get("type",{}).get("shortDetail",""),
            })
        return {"team": match["displayName"], "games": rows}
    except Exception:
        return None

def detect_entity_and_fetch_stats(market_title, category):
    """Given a market title, try to detect player/team and fetch relevant stats."""
    if category != "Sports": return None
    title_lower = market_title.lower()

    # Detect sport type
    if any(x in title_lower for x in ["nba","basketball","lakers","celtics","warriors","bulls","heat","nuggets","bucks"]):
        sport = "nba"
    elif any(x in title_lower for x in ["nfl","football","chiefs","eagles","49ers","cowboys","patriots"]):
        sport = "nfl"
    elif any(x in title_lower for x in ["mlb","baseball","yankees","dodgers","mets","cubs","red sox"]):
        sport = "mlb"
    elif any(x in title_lower for x in ["nhl","hockey","maple leafs","bruins","rangers","penguins"]):
        sport = "nhl"
    else:
        sport = "nba"  # default

    # Try to extract a name — look for capitalized word sequences
    import re
    # Common player name patterns in market titles
    words = market_title.split()
    # Try pairs and triples of capitalized words
    candidates = []
    for i in range(len(words)-1):
        if words[i][0].isupper() and words[i+1][0].isupper():
            candidates.append(f"{words[i]} {words[i+1]}")
    if len(words) > 2:
        for i in range(len(words)-2):
            if words[i][0].isupper() and words[i+1][0].isupper() and words[i+2][0].isupper():
                candidates.append(f"{words[i]} {words[i+1]} {words[i+2]}")

    # Try each candidate as a player first, then team
    for candidate in candidates:
        # Skip common non-name words
        skip = {"Will","The","NBA","NFL","MLB","NHL","Who","What","How","When","Does","Can","Is","Are"}
        if candidate.split()[0] in skip: continue
        stats = fetch_nba_player_stats(candidate)
        if stats: return {"type": "player", "sport": sport, **stats}

    # Try team
    for candidate in candidates:
        stats = fetch_espn_team_stats(candidate, sport)
        if stats: return {"type": "team", "sport": sport, **stats}

    return None

def render_stats_card(stats):
    """Render a compact stats card as HTML."""
    if not stats: return ""
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
        rows_html += "<tr>" + "".join(f"<td style='padding:6px 10px;border-bottom:1px solid #1A1A1A;color:#CCC;font-size:12px;'>{g.get(h,'-')}</td>" for h in headers) + "</tr>"

    return f"""
<div style='background:#111;border:1px solid #1E1E1E;border-left:3px solid {color};border-radius:6px;padding:12px 16px;margin-top:8px;font-family:monospace;'>
<div style='font-size:10px;color:#666;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;'>{title}</div>
<table style='width:100%;border-collapse:collapse;'>
<thead><tr>{"".join(f"<th style='padding:4px 10px;text-align:left;font-size:10px;color:#555;letter-spacing:0.06em;border-bottom:1px solid #222;'>{h}</th>" for h in headers)}</tr></thead>
<tbody>{rows_html}</tbody>
</table>
</div>"""

# ── load + split data ─────────────────────────────────────────────────────────
df_raw = load_data()
if df_raw.empty:
    st.warning("No data yet."); st.stop()

df_poly_raw   = df_raw[df_raw["source"] == "polymarket"]
df_kalshi_raw = df_raw[df_raw["source"] == "kalshi"]
df_hist_raw   = df_raw[df_raw["source"] == "kalshi_historical"]
df_live_raw   = df_raw[df_raw["source"].isin(["polymarket","kalshi"])]

df_poly_markets   = build_markets_df(df_poly_raw)   if not df_poly_raw.empty   else pd.DataFrame()
df_kalshi_markets = build_markets_df(df_kalshi_raw)  if not df_kalshi_raw.empty  else pd.DataFrame()
df_hist_markets   = build_markets_df(df_hist_raw)   if not df_hist_raw.empty   else pd.DataFrame()
df_markets        = build_markets_df(df_live_raw)

# ── sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("## QuantMarkets")
st.sidebar.markdown("<div style='font-size:11px;color:#444;margin-bottom:16px;'>Prediction market intelligence</div>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("### Data Pipeline")
st.sidebar.metric("Total snapshots", f"{len(df_raw):,}")
st.sidebar.metric("Last updated",    df_raw["timestamp"].max()[:16])
st.sidebar.markdown("**Sources**")
for src in ["polymarket","kalshi","kalshi_historical"]:
    n = df_raw[df_raw["source"] == src]["ticker"].nunique()
    st.sidebar.markdown(f"{SOURCE_LABELS[src]}: **{n:,}** markets")

# ── tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview", "🔀 Sources", "📚 Resolved",
    "🤖 AI Strategy", "🔬 Backtester", "💰 Recommender"
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("## Market Overview")

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
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Markets tracked",   f"{len(df):,}")
    c2.metric("Avg opening price", f"{df['mid_price'].mean():.2%}")
    c3.metric("Biggest mover",     f"{df['price_change_pct'].abs().max():.1f}%")
    c4.metric("Categories",        df["category"].nunique())
    c5,c6,c7,c8 = st.columns(4)
    c5.metric("Avg current price",   f"{df['current_price'].mean():.2%}")
    c6.metric("Markets moving up",   f"{len(df[df['price_change']>0]):,}")
    c7.metric("Markets moving down", f"{len(df[df['price_change']<0]):,}")
    c8.metric("Avg days to close",   f"{df['days_to_close'].mean():.0f}d" if df["days_to_close"].notna().any() else "N/A")

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
    st.markdown("### 📋 Market Browser")
    disp = df[["source","category","event_ticker","current_price","price_change_pct"]].copy()
    disp["source"]        = disp["source"].map(SOURCE_LABELS).fillna(disp["source"])
    disp["Resolves YES"]  = disp["current_price"].apply(lambda x: f"{x*100:.0f}%")
    disp["Latest Change"] = disp["price_change_pct"].apply(lambda x: f"+{x:.1f}%" if x >= 0 else f"{x:.1f}%")
    disp = disp[["source","category","event_ticker","Resolves YES","Latest Change"]]
    disp.columns = ["Source","Category","Market","Resolves YES","Latest Change"]
    st.dataframe(disp, use_container_width=True)

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

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — RESOLVED
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("## Kalshi Resolved Markets")
    if df_hist_markets.empty:
        st.info("No resolved Kalshi markets collected yet.")
    else:
        h1,h2,h3,h4 = st.columns(4)
        h1.metric("Resolved markets",     f"{len(df_hist_markets):,}")
        h2.metric("Settled YES (≥0.9)",   len(df_hist_markets[df_hist_markets["current_price"]>=0.9]))
        h3.metric("Settled NO (≤0.1)",    len(df_hist_markets[df_hist_markets["current_price"]<=0.1]))
        h4.metric("Avg settlement price", f"{df_hist_markets['current_price'].mean():.2%}")

        hc1, hc2 = st.columns(2)
        with hc1:
            bins  = [0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1.0]
            blabs = ["0-10%","10-20%","20-30%","30-40%","40-50%","50-60%","60-70%","70-80%","80-90%","90-100%"]
            hb = pd.cut(df_hist_markets["current_price"], bins=bins, labels=blabs).value_counts().sort_index().reset_index()
            hb.columns = ["Bucket","Count"]
            fig_h = px.bar(hb, x="Bucket", y="Count", color_discrete_sequence=[SOURCE_COLORS["kalshi_historical"]])
            fig_h.update_traces(hovertemplate="<b>%{x}</b><br>%{y} markets<extra></extra>")
            apply_layout(fig_h, "Settlement Price Distribution")
            st.plotly_chart(fig_h, use_container_width=True)

        with hc2:
            hcats = df_hist_markets["category"].value_counts().reset_index()
            hcats.columns = ["Category","Count"]
            fig_hc = px.bar(hcats, x="Count", y="Category", orientation="h",
                            color_discrete_sequence=[SOURCE_COLORS["kalshi_historical"]])
            fig_hc.update_traces(hovertemplate="<b>%{y}</b><br>%{x} markets<extra></extra>")
            apply_layout(fig_hc, "Resolved Markets by Category")
            st.plotly_chart(fig_hc, use_container_width=True)

        st.markdown("##### Most Recently Resolved")
        hd = df_hist_markets.sort_values("close_time", ascending=False).head(20)[
            ["event_ticker","category","mid_price","current_price","close_time"]].copy()
        hd.columns = ["Market","Category","Entry Price","Settlement Price","Closed"]
        st.dataframe(hd.reset_index(drop=True), use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — AI STRATEGY BUILDER (retail)
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("## 🤖 AI Strategy Builder")
    st.markdown(
        "<div style='color:#555;font-size:14px;margin-bottom:24px;'>"
        "Describe your strategy in plain English. AI finds matching bets right now."
        "</div>",
        unsafe_allow_html=True,
    )

    if not ANTHROPIC_API_KEY:
        st.error("Add ANTHROPIC_API_KEY to your Streamlit secrets to enable this feature.")
    else:
        examples = [
            "Buy underdog politics markets under 20%",
            "Buy contested crypto markets between 40% and 60%",
            "Buy high probability Polymarket sports above 70%",
            "Find mispriced Kalshi markets under 30%",
        ]
        ex = st.selectbox("Start from an example:", ["(type your own below)"] + examples)
        default_val = ex if ex != "(type your own below)" else ""
        user_strategy = st.text_area(
            "Describe your strategy",
            value=default_val,
            placeholder="e.g. I want to bet on underdog politics markets with low probability but high upside",
            height=90,
        )

        if st.button("🧠 Find My Bets"):
            if not user_strategy.strip():
                st.warning("Please enter a strategy.")
            else:
                with st.spinner("Analysing markets..."):
                    result = parse_strategy_with_claude(user_strategy)
                if "error" in result:
                    st.error(f"Parsing failed: {result['error']}")
                else:
                    st.session_state["ai_strategy"] = result

        if "ai_strategy" in st.session_state:
            result      = st.session_state["ai_strategy"]
            condition   = result.get("condition", "less than")
            threshold_1 = result.get("threshold_1", 0.3)
            threshold_2 = result.get("threshold_2")
            category    = result.get("category", "All")
            source      = result.get("source", "all")
            explanation = result.get("explanation", "")

            keywords = result.get("keywords", [])

            bt_base = df_markets.copy()
            if source == "polymarket":  bt_base = bt_base[bt_base["source"] == "polymarket"]
            elif source == "kalshi":    bt_base = bt_base[bt_base["source"] == "kalshi"]
            if category != "All":       bt_base = bt_base[bt_base["category"] == category]

            if condition == "less than":
                matched = bt_base[bt_base["mid_price"] < threshold_1]
            elif condition == "greater than":
                matched = bt_base[bt_base["mid_price"] > threshold_1]
            else:
                t2 = threshold_2 if threshold_2 else threshold_1
                matched = bt_base[(bt_base["mid_price"] >= threshold_1) & (bt_base["mid_price"] <= t2)]

            # semantic keyword filter — rank by how many keywords appear in the market title
            if keywords and not matched.empty:
                kws = [k.lower() for k in keywords]
                matched = matched.copy()
                matched["kw_score"] = matched["event_ticker"].str.lower().apply(
                    lambda title: sum(1 for k in kws if k in title)
                )
                # if any market matches at least 1 keyword, filter to those; otherwise keep all
                kw_matched = matched[matched["kw_score"] > 0]
                if not kw_matched.empty:
                    matched = kw_matched.sort_values("kw_score", ascending=False)
                else:
                    matched = matched.sort_values("current_price", ascending=False)
            else:
                matched = matched.sort_values("current_price", ascending=False)

            matched = matched.head(10).reset_index(drop=True)

            st.markdown("---")
            ai_left, ai_right = st.columns(2)

            with ai_left:
                st.markdown("### 💬 AI Analysis")
                if condition == "between" and threshold_2:
                    prob_rule = f"between {threshold_1:.0%} and {threshold_2:.0%}"
                elif condition == "less than":
                    prob_rule = f"below {threshold_1:.0%}"
                else:
                    prob_rule = f"above {threshold_1:.0%}"

                src_label = source.title() if source != "all" else "All"
                analysis_html = (
                    "<div style='background:#111;border:1px solid #222;border-radius:10px;"
                    "padding:20px 24px;line-height:1.8;color:#CCCCCC;font-size:14px;'>"
                    + explanation
                    + "<br><br>"
                    "<span style='color:#555;font-size:11px;text-transform:uppercase;letter-spacing:0.08em;'>RULES APPLIED</span><br>"
                    f"Probability: <b style='color:#fff'>{prob_rule}</b><br>"
                    f"Category: <b style='color:#fff'>{category}</b><br>"
                    f"Source: <b style='color:#fff'>{src_label}</b><br>"
                    f"Markets matched: <b style='color:#fff'>{len(matched)}</b>"
                    "</div>"
                )
                st.markdown(analysis_html, unsafe_allow_html=True)

                if not matched.empty:
                    st.markdown("<br>", unsafe_allow_html=True)
                    ma1, ma2 = st.columns(2)
                    safe_cp = matched["current_price"].replace(0, float("nan"))
                    ma1.metric("Avg Probability", f"{matched['current_price'].mean():.0%}")
                    ma2.metric("Avg Payout / $1", f"{(1 / safe_cp).mean():.2f}x")

            with ai_right:
                st.markdown("### 🎯 Recommended Bets")
                if matched.empty:
                    st.info("No markets matched. Try adjusting your strategy.")
                else:
                    safe_cp2 = matched["current_price"].replace(0, float("nan"))
                    matched["payout"]       = (1 / safe_cp2).round(2)
                    matched["resolves_yes"] = matched["current_price"].apply(lambda x: f"{x*100:.0f}%")
                    matched["change"]       = matched["price_change_pct"].apply(
                        lambda x: f"+{x:.1f}%" if x >= 0 else f"{x:.1f}%"
                    )

                    def make_ai_link(row):
                        if row["source"] == "polymarket":
                            return f'<a href="https://polymarket.com/event/{row["ticker"]}" target="_blank">Bet →</a>'
                        elif row["source"] == "kalshi":
                            return f'<a href="https://kalshi.com/markets/{row["ticker"]}" target="_blank">Bet →</a>'
                        return ""

                    matched["link"] = matched.apply(make_ai_link, axis=1)
                    disp = matched[["event_ticker", "resolves_yes", "payout", "change", "link"]].copy()
                    disp.columns = ["Market", "Resolves YES", "Payout/$1", "Recent Change", "🔗"]
                    st.write(disp.to_html(escape=False, index=False), unsafe_allow_html=True)

                    # stats cards for sports/politics markets
                    if category == "Sports":
                        st.markdown("<div style='margin-top:16px;font-size:11px;color:#555;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;'>RECENT STATS</div>", unsafe_allow_html=True)
                        shown = set()
                        for _, row in matched.iterrows():
                            with st.spinner(f"Fetching stats for {row['event_ticker'][:40]}..."):
                                stats = detect_entity_and_fetch_stats(row["event_ticker"], category)
                            if stats:
                                key = stats.get("player") or stats.get("team","")
                                if key not in shown:
                                    shown.add(key)
                                    st.markdown(render_stats_card(stats), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("↩ Try a different strategy"):
                del st.session_state["ai_strategy"]
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — INSTITUTIONAL BACKTESTER
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("## 🔬 Institutional Backtester")
    st.markdown(
        "<div style='color:#555;font-size:14px;margin-bottom:24px;'>"
        "Paste your Python algorithm below. We run it against resolved Kalshi markets and return full performance metrics."
        "</div>",
        unsafe_allow_html=True,
    )

    howto_html = (
        "<div style='background:#111;border:1px solid #1E1E1E;border-left:3px solid #3B82F6;"
        "border-radius:8px;padding:16px 20px;font-size:13px;color:#888;margin-bottom:24px;'>"
        "<b style='color:#fff'>How it works:</b> Define a function called "
        "<code>run_strategy(markets)</code> that receives a DataFrame of resolved markets "
        "and returns a list of trade dicts with keys: "
        "<code>ticker</code>, <code>entry_price</code>, <code>exit_price</code>, <code>size</code>."
        "</div>"
    )
    st.markdown(howto_html, unsafe_allow_html=True)

    default_code = """\
def run_strategy(markets):
    \"\"\"
    markets: DataFrame with columns:
      ticker, event_ticker, category,
      mid_price (entry), current_price (settlement), close_time

    Return a list of trade dicts:
      [{"ticker": ..., "entry_price": ..., "exit_price": ..., "size": 10}, ...]
    \"\"\"
    trades = []
    for _, row in markets.iterrows():
        # Example: buy any market priced below 30%
        if row["mid_price"] < 0.30:
            trades.append({
                "ticker":      row["ticker"],
                "market":      row["event_ticker"],
                "category":    row["category"],
                "entry_price": row["mid_price"],
                "exit_price":  row["current_price"],
                "size":        10,
            })
    return trades
"""

    user_code = st.text_area("Your strategy function", value=default_code, height=340)

    hist_cats = sorted(df_hist_markets["category"].unique().tolist()) if not df_hist_markets.empty else []
    bt_cat_inst = st.selectbox("Filter by category", ["All"] + hist_cats, key="inst_cat")

    if st.button("▶ Run Backtest", key="inst_run"):
        if df_hist_markets.empty:
            st.warning("No resolved Kalshi markets available yet. Check back after more data is collected.")
        else:
            try:
                hist = df_hist_markets.copy()
                if bt_cat_inst != "All":
                    hist = hist[hist["category"] == bt_cat_inst]

                if hist.empty:
                    st.warning("No resolved markets in that category.")
                else:
                    local_ns = {}
                    exec(user_code, {"pd": pd}, local_ns)

                    if "run_strategy" not in local_ns:
                        st.error("Your code must define a function called run_strategy(markets).")
                    else:
                        with st.spinner("Running backtest on resolved markets..."):
                            trades = local_ns["run_strategy"](hist)

                        if not trades:
                            st.warning("Your strategy returned no trades. Try relaxing the conditions.")
                        else:
                            trades_df = pd.DataFrame(trades)
                            required  = {"ticker", "entry_price", "exit_price", "size"}
                            if not required.issubset(trades_df.columns):
                                st.error(f"Each trade needs keys: {required}. Got: {set(trades_df.columns)}")
                            else:
                                trades_df["pnl"] = (
                                    (trades_df["exit_price"] - trades_df["entry_price"])
                                    / trades_df["entry_price"]
                                ) * trades_df["size"]
                                trades_df["pnl"]            = trades_df["pnl"].round(4)
                                trades_df["win"]            = trades_df["pnl"] > 0
                                trades_df["cumulative_pnl"] = trades_df["pnl"].cumsum()

                                total_pnl  = trades_df["pnl"].sum()
                                win_rate   = trades_df["win"].mean()
                                n_trades   = len(trades_df)
                                total_size = trades_df["size"].sum()
                                returns    = trades_df["pnl"] / trades_df["size"]
                                sharpe     = (
                                    (returns.mean() / returns.std() * (252 ** 0.5))
                                    if returns.std() > 0 else 0.0
                                )

                                st.markdown("---")
                                st.markdown(f"### Results — {n_trades:,} trades executed")
                                bm1, bm2, bm3, bm4 = st.columns(4)
                                bm1.metric("Total P&L",    f"${total_pnl:+.2f}")
                                bm2.metric("Win Rate",     f"{win_rate:.0%}")
                                bm3.metric("Sharpe Ratio", f"{sharpe:.2f}")
                                bm4.metric("Capital Used", f"${total_size:,.0f}")

                                fig_pnl = go.Figure()
                                fig_pnl.add_trace(go.Scatter(
                                    x=trades_df.index,
                                    y=trades_df["cumulative_pnl"],
                                    mode="lines",
                                    line=dict(color="#3B82F6", width=2),
                                    fill="tozeroy",
                                    fillcolor="rgba(59,130,246,0.08)",
                                    hovertemplate="Trade %{x}<br>Cumulative P&L: $%{y:.2f}<extra></extra>",
                                ))
                                fig_pnl.add_hline(y=0, line_color="#333333", line_width=1)
                                apply_layout(fig_pnl, "Cumulative P&L ($)", height=340)
                                st.plotly_chart(fig_pnl, use_container_width=True)

                                st.markdown("### Trade Breakdown")
                                if "market" in trades_df.columns:
                                    show_cols = ["market", "category", "entry_price", "exit_price", "size", "pnl", "win"]
                                else:
                                    show_cols = ["ticker", "entry_price", "exit_price", "size", "pnl", "win"]
                                breakdown = trades_df[show_cols].copy()
                                breakdown["entry_price"] = breakdown["entry_price"].apply(lambda x: f"{x:.2%}")
                                breakdown["exit_price"]  = breakdown["exit_price"].apply(lambda x: f"{x:.2%}")
                                breakdown["pnl"]         = breakdown["pnl"].apply(
                                    lambda x: f"+${x:.2f}" if x >= 0 else f"-${abs(x):.2f}"
                                )
                                breakdown["win"]  = breakdown["win"].apply(lambda x: "✅" if x else "❌")
                                breakdown.columns = [c.replace("_", " ").title() for c in breakdown.columns]
                                st.dataframe(breakdown.reset_index(drop=True), use_container_width=True)

            except Exception as e:
                st.error(f"Error running your strategy: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 6 — RECOMMENDER
# ─────────────────────────────────────────────────────────────────────────────
with tab6:
    st.markdown("## Smart Bet Recommender")
    st.markdown("<div style='color:#555;font-size:14px;margin-bottom:24px;'>Set your budget and risk tolerance — we'll find the best markets right now.</div>", unsafe_allow_html=True)

    rc1,rc2,rc3 = st.columns(3)
    with rc1: budget = st.number_input("Budget ($)", min_value=10, max_value=100000, value=100, step=10)
    with rc2: target_return = st.number_input("Target profit ($)", min_value=5, max_value=100000, value=50, step=5)
    with rc3: risk_level = st.selectbox("Risk tolerance", ["Low","Medium","High"])

    rec_src = st.selectbox("Source", ["All (Polymarket + Kalshi)","Polymarket only","Kalshi only"], key="rec_src")
    rec_cat = st.selectbox("Category", ["All"]+sorted(df_markets["category"].unique().tolist()), key="rec_cat")

    if st.button("🎯 Find Best Bets"):
        if risk_level == "Low":
            rec_df = df_markets[(df_markets["current_price"]>=0.65)&(df_markets["current_price"]<=0.95)]
            risk_label = "Low risk — high probability"
        elif risk_level == "Medium":
            rec_df = df_markets[(df_markets["current_price"]>=0.35)&(df_markets["current_price"]<=0.65)]
            risk_label = "Medium risk — contested"
        else:
            rec_df = df_markets[(df_markets["current_price"]>=0.05)&(df_markets["current_price"]<=0.35)]
            risk_label = "High risk — contrarian"

        if "Polymarket only" in rec_src: rec_df = rec_df[rec_df["source"]=="polymarket"]
        elif "Kalshi only"   in rec_src: rec_df = rec_df[rec_df["source"]=="kalshi"]
        if rec_cat != "All": rec_df = rec_df[rec_df["category"]==rec_cat]

        if rec_df.empty:
            st.warning("No markets match. Try adjusting filters.")
        else:
            rec_df = rec_df.copy()
            rec_df["payout_if_yes"] = (1/rec_df["current_price"]).round(2)
            rec_df = rec_df.sort_values("current_price", ascending=False).reset_index(drop=True)
            max_bets = min(10, len(rec_df))
            rec_df   = rec_df.head(max_bets)
            rec_df["bet_amount"]       = round(budget/max_bets, 2)
            rec_df["potential_profit"] = ((rec_df["payout_if_yes"]-1)*rec_df["bet_amount"]).round(2)

            def make_link(row):
                if row["source"]=="polymarket": return f'<a href="https://polymarket.com/event/{row["ticker"]}" target="_blank">Place Bet →</a>'
                elif row["source"]=="kalshi":   return f'<a href="https://kalshi.com/markets/{row["ticker"]}" target="_blank">Place Bet →</a>'
                return ""
            rec_df["link"] = rec_df.apply(make_link, axis=1)

            st.markdown(f"### Top Bets — {risk_label}")
            s1,s2,s3 = st.columns(3)
            s1.metric("Markets found",     len(rec_df))
            s2.metric("Avg probability",   f"{rec_df['current_price'].mean():.2%}")
            s3.metric("Avg payout per $1", f"{rec_df['payout_if_yes'].mean():.2f}x")

            bd = rec_df[["event_ticker","source","category","current_price","payout_if_yes","bet_amount","potential_profit","close_time","link"]].copy()
            bd["source"] = bd["source"].map(SOURCE_LABELS).fillna(bd["source"])
            bd.columns   = ["Market","Source","Category","Probability","Payout/$ 1","Bet ($)","Profit ($)","Closes","🔗"]
            st.write(bd.to_html(escape=False, index=False), unsafe_allow_html=True)

            total_bet, total_profit = rec_df["bet_amount"].sum(), rec_df["potential_profit"].sum()
            st.markdown("---")
            p1,p2,p3 = st.columns(3)
            p1.metric("Capital deployed",   f"${total_bet:.2f}")
            p2.metric("% of budget used",   f"{(total_bet/budget*100):.1f}%")
            p3.metric("Total potential profit", f"${total_profit:.2f}")

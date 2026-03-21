import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from supabase import create_client

st.set_page_config(page_title="Callibr", page_icon="🎯", layout="wide")

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
    <div style="font-size:10px;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;color:#444444;margin-bottom:10px;">PREDICTION MARKET INTELLIGENCE</div>
    <div style="font-size:38px;font-weight:700;color:#FFFFFF;letter-spacing:-0.03em;line-height:1;">Callibr</div>
    <div style="font-size:14px;color:#444444;margin-top:10px;font-weight:400;letter-spacing:0.01em;">Find mispriced markets · Research any bet · Get your edge</div>
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
    all_rows, offset, batch_size = [], 0, 1000
    while True:
        batch = supabase.table("market_prices").select("*")\
            .neq("source", "kalshi_historical")\
            .gte("close_time", cutoff)\
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
        # Get team schedule/results — completed games only
        sched = requests.get(
            f"https://site.api.espn.com/apis/site/v2/sports/{s}/{league}/teams/{tid}/schedule",
            timeout=8
        ).json()
        all_events = sched.get("events", [])
        # filter to only completed games
        completed = [
            e for e in all_events
            if e.get("competitions",[{}])[0].get("status",{}).get("type",{}).get("completed", False)
        ]
        events = completed[-5:] if completed else []
        rows = []
        for e in events:
            comp = e.get("competitions",[{}])[0]
            comps = comp.get("competitors",[])
            home = next((c for c in comps if c.get("homeAway")=="home"), {})
            away = next((c for c in comps if c.get("homeAway")=="away"), {})
            # determine W/L for this team
            team_comp = next((c for c in comps if tid in str(c.get("team",{}).get("id",""))), {})
            result = "W" if team_comp.get("winner") else "L"
            rows.append({
                "Date":   e.get("date","")[:10],
                "Home":   home.get("team",{}).get("abbreviation","?"),
                "Away":   away.get("team",{}).get("abbreviation","?"),
                "Score":  f"{home.get('score','?')}-{away.get('score','?')}",
                "W/L":    result,
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
df_live_raw   = df_raw[df_raw["source"].isin(["polymarket","kalshi"])]

df_poly_markets   = build_markets_df(df_poly_raw)   if not df_poly_raw.empty   else pd.DataFrame()
df_kalshi_markets = build_markets_df(df_kalshi_raw)  if not df_kalshi_raw.empty  else pd.DataFrame()
df_markets        = build_markets_df(df_live_raw)

# ── sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("## Callibr")
st.sidebar.markdown("<div style='font-size:11px;color:#444;margin-bottom:16px;'>Find your edge</div>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("### Data Pipeline")
st.sidebar.metric("Total snapshots", f"{len(df_raw):,}")
st.sidebar.metric("Last updated",    df_raw["timestamp"].max()[:16])
st.sidebar.markdown("**Sources**")
for src in ["polymarket","kalshi","kalshi_historical"]:
    n = df_raw[df_raw["source"] == src]["ticker"].nunique()
    st.sidebar.markdown(f"{SOURCE_LABELS[src]}: **{n:,}** markets")

# ── tabs ──────────────────────────────────────────────────────────────────────
tab1, tab4, tab2 = st.tabs([
    "📊 Overview", "🔍 Market Research", "🔀 Sources"
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
    # ── helper to render a market table ──────────────────────────────────────
    def render_market_table(df_t):
        if df_t.empty:
            st.info("No markets match current filters.")
            return
        disp = df_t[["source","category","event_ticker","current_price","price_change_pct","days_to_close"]].copy()
        disp["Source"]       = disp["source"].map(SOURCE_LABELS).fillna(disp["source"])
        disp["Resolves YES"] = disp["current_price"].apply(lambda x: f"{x*100:.0f}%")
        disp["Change"]       = disp["price_change_pct"].apply(lambda x: f"+{x:.1f}%" if x >= 0 else f"{x:.1f}%")
        disp["Closes in"]    = disp["days_to_close"].apply(
            lambda d: f"{int(d)}d" if pd.notna(d) and d >= 0 else ("Expired" if pd.notna(d) else "—")
        )
        disp = disp[["Source","category","event_ticker","Resolves YES","Change","Closes in"]]
        disp.columns = ["Source","Category","Market","Resolves YES","Change","Closes in"]
        st.dataframe(disp.reset_index(drop=True), use_container_width=True)

    # ── Sports Games This Week ────────────────────────────────────────────────
    sports_week = (
        df_markets[
            (df_markets["category"] == "Sports") &
            (df_markets["days_to_close"].between(0, 14))
        ]
        .sort_values("days_to_close", ascending=True)
    )
    if not sports_week.empty:
        st.markdown(f"### Sports &amp; Games — Next 14 Days &nbsp;<span style='font-size:14px;color:#555;font-weight:400;'>({len(sports_week):,} markets)</span>", unsafe_allow_html=True)
        st.caption("All sports game markets closing within 14 days, sorted by closest first.")
        render_market_table(sports_week)
        st.markdown("---")

    # Split into upcoming (≤30 days) and long-term (>30 days)
    upcoming = df[df["days_to_close"].between(0, 30)].sort_values("days_to_close", ascending=True)
    longterm  = df[df["days_to_close"] > 30].sort_values("days_to_close", ascending=True)
    no_date   = df[df["days_to_close"].isna()]

    # ── Upcoming ─────────────────────────────────────────────────────────────
    st.markdown(f"### ⚡ Upcoming — Next 30 Days &nbsp;<span style='font-size:14px;color:#555;font-weight:400;'>({len(upcoming):,} markets)</span>", unsafe_allow_html=True)
    st.caption("Sorted by urgency — closest to closing first.")
    render_market_table(upcoming)

    st.markdown("---")

    # ── Long-term ─────────────────────────────────────────────────────────────
    with st.expander(f"📅  Long-term Markets — 30+ Days  ({len(longterm):,} markets)", expanded=False):
        st.caption("Sorted by closest close date first.")
        render_market_table(longterm)

    # ── No close date ─────────────────────────────────────────────────────────
    if not no_date.empty:
        with st.expander(f"❔  No Close Date  ({len(no_date):,} markets)", expanded=False):
            render_market_table(no_date)

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
_NOISE_PATTERNS = [
    # In-game timing markets
    "first half", "1st half", "second half", "2nd half",
    "first quarter", "1st quarter", "second quarter", "2nd quarter",
    "third quarter", "3rd quarter", "fourth quarter", "4th quarter",
    "first period", "1st period", "second period", "2nd period", "third period", "3rd period",
    "halftime", "half time", "half-time",
    # Next-event micro-markets
    "next goal", "next score", "next basket", "next point", "next touchdown",
    "next team to score", "anytime scorer",
    # Announcer / broadcast novelty markets
    "announcer", "will the announcer", "commentator",
    "will anyone say", "will a player say", "will the broadcast",
    "will the crowd", "will fans",
    # Celebration / entertainment props
    "celebration", "will celebrate", "dunk celebration",
    "will shake hands", "will hug",
    # Injury/ejection props that aren't pre-game
    "will be ejected", "will get ejected", "will be removed",
    # Misc live noise
    "live ", "in-game", "in game",
]

# Patterns that signal a meaningful, researchable market — get a score boost
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

def compute_edge_score(row, df_all):
    """
    Edge Score 0-100. Higher = more likely mispriced / worth researching.
    Returns 0 immediately for:
      - Markets already at near-certain prices (resolving, not mispriced)
      - Novelty/announcer/micro-markets (no research value)
    Boosts markets about game outcomes, winners, totals, spreads.
    """
    cp = row.get("current_price", 0.5)
    title = row.get("event_ticker", "").lower()

    # Hard disqualifiers — these are not research-worthy
    # 1. Market is resolving — price at extremes means it's effectively decided
    if cp <= 0.15 or cp >= 0.85:
        return 0

    # 2. Novelty / micro-market — no research value
    # Exception: game mention markets (contain " vs ") get a floor of 10 so
    # they surface as "game scheduled" indicators in search results
    if any(p in title for p in _NOISE_PATTERNS):
        return 10 if " vs " in title else 0

    score = 40.0  # baseline (lower than before — earn it)

    # 1. Opening vs current divergence — the core signal
    mid = row.get("mid_price", cp)
    divergence = abs(cp - mid)
    score += min(divergence * 80, 25)  # max +25

    # 2. Price drift vs category peers — moved more than average = interesting
    cat = row.get("category", "Other")
    cat_avg_change = df_all[df_all["category"] == cat]["price_change_pct"].mean()
    own_change = row.get("price_change_pct", 0)
    drift_delta = abs(own_change - cat_avg_change)
    score += min(drift_delta * 0.6, 15)  # max +15

    # 3. Contrarian signal — moderate extremes are interesting, but not resolving ones
    # (resolving ones already killed above at 15%/85%)
    if cp < 0.25 or cp > 0.75:
        score += 8   # crowd may be overconfident at these levels
    elif 0.38 <= cp <= 0.62:
        score -= 8   # toss-up markets are less interesting for edge finding

    # 4. Signal boost — meaningful market types (winner, total, spread, etc.)
    if any(p in title for p in _SIGNAL_PATTERNS):
        score += 10

    # 5. Proximity to close — urgency bonus
    days = row.get("days_to_close", 30)
    if days is not None and not pd.isna(days):
        if days <= 3:    score += 12
        elif days <= 7:  score += 7
        elif days <= 14: score += 3

    # 6. Liquidity signal — more snapshots = market is being watched
    snap = row.get("snapshot_count", 1)
    if snap >= 5: score += 5
    elif snap <= 1: score -= 5

    return min(max(round(score), 0), 100)

def edge_score_color(score):
    if score >= 75: return "#00C2A8"   # teal — strong edge
    elif score >= 55: return "#F59E0B" # amber — moderate
    else: return "#555555"              # grey — weak

def edge_score_label(score):
    if score >= 75: return "STRONG EDGE"
    elif score >= 55: return "MODERATE"
    else: return "WEAK"

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
def generate_market_research(market_title, current_price, category, edge_score, price_change_pct, news_headlines, today_date="", player_stats_summary=""):
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

    stats_block = f"\nRecent player/team stats:\n{player_stats_summary}" if player_stats_summary else ""

    prompt = f"""Market: {market_title}
Current probability: {current_price:.1%}
Category: {category}
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
            narrative_html = f"""<div style="background:#1A0F00;border:1px solid #F59E0B44;border-left:3px solid #F59E0B;border-radius:6px;padding:14px;margin-bottom:12px;">
  <div style="font-size:10px;color:#F59E0B;letter-spacing:0.1em;font-weight:700;text-transform:uppercase;margin-bottom:4px;">⚠️ Narrative Gap Detected</div>
  <div style="font-size:12px;color:#CCC;">{narrative_reason}</div>
</div>"""

        verdict_html = f"""
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px;">
  <div style="background:#111;border:1px solid #1E1E1E;border-radius:8px;padding:16px;text-align:center;">
    <div style="font-size:10px;color:#555;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">Current Price</div>
    <div style="font-size:28px;font-weight:700;color:#fff;">{cp:.0%}</div>
  </div>
  <div style="background:#111;border:1px solid #1E1E1E;border-radius:8px;padding:16px;text-align:center;">
    <div style="font-size:10px;color:#555;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">Fair Value</div>
    <div style="font-size:28px;font-weight:700;color:{diff_color};">{fv:.0%} <span style="font-size:14px;">({diff_str})</span></div>
  </div>
  <div style="background:#111;border:1px solid {vc};border-radius:8px;padding:16px;text-align:center;">
    <div style="font-size:10px;color:#555;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">Verdict</div>
    <div style="font-size:18px;font-weight:700;color:{vc};">{verdict}</div>
    <div style="font-size:10px;color:#555;margin-top:4px;">{confidence} confidence</div>
  </div>
</div>

<div style="background:#0D0D0D;border:1px solid #1A1A1A;border-radius:8px;padding:16px;margin-bottom:12px;">
  <div style="font-size:10px;color:#555;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:10px;">📊 Confidence Band — Fair Value Range</div>
  <div style="display:flex;justify-content:space-between;font-size:11px;color:#666;margin-bottom:6px;">
    <span>Bear {bear_left}</span>
    <span style="color:#FFF;font-weight:600;">Fair Value {fv_pct}</span>
    <span>Bull {bull_right}</span>
  </div>
  <div style="background:#1A1A1A;border-radius:4px;height:8px;position:relative;overflow:hidden;">
    <div style="position:absolute;left:0;top:0;height:100%;width:100%;background:linear-gradient(90deg,#DC2626 0%,#F59E0B 50%,#00C2A8 100%);opacity:0.3;border-radius:4px;"></div>
    <div style="position:absolute;left:{fv_pos:.0f}%;top:-2px;width:3px;height:12px;background:#FFF;border-radius:2px;transform:translateX(-50%);"></div>
  </div>
  <div style="font-size:10px;color:#444;margin-top:6px;text-align:center;">If correct, current price of {cp:.0%} is outside this range → potential edge</div>
</div>

<div style="background:#0D0D0D;border:1px solid #1A1A1A;border-left:3px solid {vc};border-radius:6px;padding:16px;margin-bottom:12px;">
  <div style="font-size:11px;color:#888;line-height:1.7;">{reasoning}</div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px;">
  <div style="background:#0D0D0D;border:1px solid #1A1A1A;border-radius:6px;padding:12px;">
    <div style="font-size:10px;color:#555;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Key Risk</div>
    <div style="font-size:12px;color:#CCC;">{key_risk}</div>
  </div>
  <div style="background:#0D0D0D;border:1px solid #1A1A1A;border-radius:6px;padding:12px;">
    <div style="font-size:10px;color:#555;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Historical Base Rate</div>
    <div style="font-size:12px;color:#CCC;">{base_rate}</div>
  </div>
  <div style="background:#0D0D0D;border:1px solid {liq_color}22;border-radius:6px;padding:12px;">
    <div style="font-size:10px;color:#555;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Liquidity</div>
    <div style="font-size:13px;font-weight:700;color:{liq_color};">{liq_label}</div>
    <div style="font-size:10px;color:#555;margin-top:2px;">{liq_desc}</div>
  </div>
</div>
{narrative_html}"""
    else:
        verdict_html = f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;">
  <div style="background:#111;border:1px solid #1E1E1E;border-radius:8px;padding:16px;text-align:center;">
    <div style="font-size:10px;color:#555;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">Current Price</div>
    <div style="font-size:28px;font-weight:700;color:#fff;">{cp:.0%}</div>
  </div>
  <div style="background:#111;border:1px solid #1E1E1E;border-radius:8px;padding:16px;text-align:center;">
    <div style="font-size:10px;color:#555;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">Edge Score</div>
    <div style="font-size:28px;font-weight:700;color:{ec};">{edge_score}</div>
  </div>
</div>"""

    # news block
    if news:
        news_items = ""
        for a in news[:4]:
            news_items += f"""<div style="padding:10px 0;border-bottom:1px solid #151515;">
  <a href="{a['url']}" target="_blank" style="font-size:13px;color:#E0E0E0;text-decoration:none;font-weight:500;line-height:1.4;">{a['title']}</a>
  <div style="font-size:10px;color:#444;margin-top:4px;">{a['source']} · {a['published']}</div>
</div>"""
        news_html = f"""<div style="margin-bottom:16px;">
<div style="font-size:10px;color:#555;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px;">📰 Recent News</div>
{news_items}
</div>"""
    else:
        news_html = '<div style="font-size:12px;color:#444;margin-bottom:16px;">No recent news found for this market.</div>'

    card = f"""
<div style="background:#111111;border:1px solid #1E1E1E;border-radius:12px;padding:24px;margin-bottom:16px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;">
    <div style="flex:1;margin-right:16px;">
      <div style="font-size:10px;color:#444;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;">{src_label} · {row['category']}</div>
      <div style="font-size:16px;font-weight:600;color:#FFF;line-height:1.4;">{row['event_ticker']}</div>
    </div>
    <div style="display:flex;align-items:center;gap:12px;flex-shrink:0;">
      <div style="text-align:center;">
        <div style="font-size:9px;color:#444;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:3px;">EDGE</div>
        <div style="font-size:20px;font-weight:700;color:{ec};">{edge_score}</div>
        <div style="font-size:9px;color:{ec};letter-spacing:0.06em;">{edge_score_label(edge_score)}</div>
      </div>
      <a href="{bet_url}" target="_blank" style="background:#FFF;color:#000;font-size:11px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;padding:10px 20px;border-radius:5px;text-decoration:none;">Bet →</a>
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
        "<div style='color:#555;font-size:14px;margin-bottom:28px;'>Search any topic. We surface live markets, score each edge opportunity, pull recent news, and give you a verdict.</div>",
        unsafe_allow_html=True,
    )

    # ── search + filters ──────────────────────────────────────────────────────
    sr1, sr2, sr3 = st.columns([3, 1, 1])
    with sr1:
        search_query = st.text_input("", placeholder="Search markets — e.g. 'LeBron', 'Trump', 'Bitcoin ETF', 'Lakers'...", key="research_query", label_visibility="collapsed")
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
        # Team nickname → city name aliases used in Kalshi/Polymarket event titles
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
            "lakers": ["los angeles"], "clippers": ["los angeles"],
            "suns": ["phoenix"], "kings": ["sacramento"],
            "mavericks": ["dallas"], "mavs": ["dallas"],
            "rockets": ["houston"], "grizzlies": ["memphis"],
            "pelicans": ["new orleans"], "spurs": ["san antonio"],
        }
        def _term_matches(title, term):
            if term in _TEAM_ALIASES:
                return term in title or any(a in title for a in _TEAM_ALIASES[term])
            return term in title

        terms = [t for t in search_query.lower().split() if len(t) > 1 and t not in _search_stop]
        if not terms:
            terms = [t for t in search_query.lower().split() if len(t) > 1]  # fallback if all stripped

        # AND logic — all meaningful terms must appear in the market title (alias-aware)
        mask = df_res["event_ticker"].str.lower().apply(lambda t: all(_term_matches(t, term) for term in terms))
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
            mask_partial = df_res_base["event_ticker"].str.lower().apply(
                lambda t: sum(1 for term in terms if _term_matches(t, term)) >= min_matches
            )
            df_res = df_res_base[mask_partial]
            if not df_res.empty:
                st.caption(f"No exact matches — showing markets containing at least {min_matches} of: {', '.join(terms)}")

    # ── compute edge scores ───────────────────────────────────────────────────
    if not df_res.empty:
        df_res = df_res.copy()
        df_res["edge_score"] = df_res.apply(lambda r: compute_edge_score(r, df_markets), axis=1)
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
            if any(t.startswith(p) for p in ["KXNBAGAME","KXNCAABBGAME","KXNCAAWBGAME","KXNHLGAME","KXMLSGAME"]):
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

        # Always include all near-term markets (≤7 days), fill remainder up to 80 from the rest
        near_term = df_res[df_res["days_to_close"].between(0, 7, inclusive="both")]
        the_rest   = df_res[~df_res.index.isin(near_term.index)]
        display_df = pd.concat([near_term, the_rest]).head(200).copy()
        _closes_dt = pd.to_datetime(display_df["close_time"], errors="coerce", utc=True)
        display_df["Closes"] = _closes_dt.dt.strftime("%d %b").str.lstrip("0").replace("", "—")
        display_df["enriched_title"] = display_df.apply(
            lambda r: enrich_title_with_context(r["event_ticker"], r["ticker"], r.get("close_time", "")), axis=1
        )
        display_df["game_key"] = display_df.apply(
            lambda r: extract_game_key(r["ticker"], r["event_ticker"]), axis=1
        )
        display_df["market_type"] = display_df["ticker"].apply(get_market_type)

        # ── Unified game card + expander view ─────────────────────────────────
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
            .sort_values(["min_days", "best_edge"], ascending=[True, False], na_position="last")
        )

        st.markdown("### Games & Events")
        for game_key, meta in game_meta.iterrows():
            grp = display_df[display_df["game_key"] == game_key]

            # Representative title: prefer a game/match winner row
            winner_rows = grp[grp["market_type"].isin(["Game Winner", "Match Winner"])]
            game_title = (winner_rows.iloc[0]["event_ticker"] if not winner_rows.empty
                          else grp.iloc[0]["enriched_title"])

            best_edge  = int(meta["best_edge"])
            min_days   = meta["min_days"]
            n_markets  = int(meta["n_markets"])
            closes     = meta["closes"]
            src_icons  = " ".join(grp["source"].map({"polymarket": "🟣", "kalshi": "🔵"}).dropna().unique())

            badge = (" 🟢 TODAY" if pd.notna(min_days) and min_days <= 0
                     else " 🟡 THIS WEEK" if pd.notna(min_days) and min_days <= 3
                     else "")

            types_in_grp = [t for t in _TYPE_ORDER if t in grp["market_type"].values]
            type_chips = "  ".join(
                f'<span style="background:#1A1A1A;color:#777;font-size:9px;padding:2px 6px;border-radius:3px;">{t}</span>'
                for t in types_in_grp
            )

            exp_label = f"{game_title}{badge}  ·  {closes}  ·  {n_markets} market{'s' if n_markets != 1 else ''}"
            auto_open = pd.notna(min_days) and min_days <= 1

            with st.expander(exp_label, expanded=auto_open):
                st.markdown(
                    f'<div style="margin-bottom:10px;font-size:11px;color:#555;">'
                    f'{src_icons} &nbsp; {type_chips}</div>',
                    unsafe_allow_html=True
                )
                for mtype in _TYPE_ORDER:
                    type_rows = grp[grp["market_type"] == mtype].sort_values("edge_score", ascending=False)
                    if type_rows.empty:
                        continue
                    st.markdown(
                        f'<div style="font-size:9px;color:#444;letter-spacing:0.1em;text-transform:uppercase;'
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
                        title_txt = bet["event_ticker"]
                        src       = bet["source"]
                        bet_url   = (
                            f"https://polymarket.com/event/{bet['ticker']}"
                            if src == "polymarket"
                            else f"https://kalshi.com/markets/{str(bet['ticker']).split('-')[0].lower()}"
                        )
                        _rc = st.columns([5, 1, 1, 1, 1, 2])
                        _rc[0].markdown(
                            f'<div style="font-size:13px;color:#CCC;padding:4px 0;">{title_txt}</div>',
                            unsafe_allow_html=True
                        )
                        _rc[1].markdown(
                            f'<div style="font-size:13px;color:#FFF;font-weight:600;padding:4px 0;">{cp:.0%}</div>',
                            unsafe_allow_html=True
                        )
                        _rc[2].markdown(
                            f'<div style="font-size:12px;color:{chg_color};padding:4px 0;">{chg_str}</div>',
                            unsafe_allow_html=True
                        )
                        _rc[3].markdown(
                            f'<div style="font-size:12px;font-weight:700;color:{bec};padding:4px 0;">{es}</div>',
                            unsafe_allow_html=True
                        )
                        _rc[4].markdown(
                            f'<a href="{bet_url}" target="_blank" style="font-size:10px;background:#FFF;'
                            f'color:#000;padding:4px 8px;border-radius:3px;font-weight:700;'
                            f'text-decoration:none;display:inline-block;margin-top:2px;">Bet →</a>',
                            unsafe_allow_html=True
                        )
                        if _rc[5].button("🔬 Research", key=f"dr_{bet['ticker']}", help="Run deep research"):
                            st.session_state["dr_ticker"] = bet["ticker"]

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
                    _dr_news_q  = build_news_query(_dr_row["event_ticker"], _dr_row["category"])
                    _dr_news    = fetch_news(_dr_news_q, max_articles=5)
                    _dr_stats   = detect_entity_and_fetch_stats(_dr_row["event_ticker"], _dr_row["category"])
                    _dr_st_txt  = ""
                    if _dr_stats and _dr_stats.get("games"):
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
                    )
                if _dr_research and _dr_research.get("_error"):
                    st.error(f"⚠️ AI verdict failed: {_dr_research['_error']}")
                    _dr_research = None
                st.session_state["research_card"]  = render_research_card(_dr_row, _dr_research, _dr_news, _dr_edge, df_markets)
                st.session_state["research_sports"] = render_stats_card(_dr_stats) if _dr_stats else ""
            st.session_state["dr_ticker"] = None

        st.markdown("---")
        st.markdown("### 🔬 Deep Research")
        st.markdown("<div style='color:#444;font-size:12px;margin-bottom:16px;'>Select any market for full AI analysis — news, fair value, and mispricing verdict.</div>", unsafe_allow_html=True)

        # Market selector — sorted by game (closest first), grouped with market type context
        # Sort display_df by game_key order (same order as the expanders above)
        _game_order = list(game_meta.index)
        _gk_rank = {gk: i for i, gk in enumerate(_game_order)}
        _type_rank = {t: i for i, t in enumerate(_TYPE_ORDER)}
        _sel_df = display_df.copy()
        _sel_df["_gk_rank"] = _sel_df["game_key"].map(_gk_rank).fillna(999)
        _sel_df["_mt_rank"] = _sel_df["market_type"].map(_type_rank).fillna(99)
        _sel_df = _sel_df.sort_values(["_gk_rank", "_mt_rank", "edge_score"], ascending=[True, True, False])

        market_labels  = [
            f"{row['event_ticker']}  ·  {row['market_type']}  ·  {row['current_price']:.0%}"
            for _, row in _sel_df.iterrows()
        ]
        market_options = _sel_df["event_ticker"].tolist()
        label_to_ticker = dict(zip(market_labels, market_options))

        selected_label  = st.selectbox("Select market to research", market_labels, key="res_market_select")
        selected_market = label_to_ticker.get(selected_label, market_options[0] if market_options else "")

        if st.button("🔬 Run Deep Research", key="run_research"):
            row = df_res[df_res["event_ticker"] == selected_market].iloc[0]
            edge = int(row["edge_score"])

            with st.spinner("Fetching news and generating analysis..."):
                news_query   = build_news_query(row["event_ticker"], row["category"])
                news         = fetch_news(news_query, max_articles=5)
                sports_stats = detect_entity_and_fetch_stats(row["event_ticker"], row["category"])
                # Build compact stats summary for AI prompt
                stats_text = ""
                if sports_stats and sports_stats.get("games"):
                    games = sports_stats["games"]
                    if sports_stats["type"] == "player":
                        stats_text = (
                            f"{sports_stats['player']} ({sports_stats.get('team','')}) "
                            f"last {len(games)} games: " +
                            ", ".join([f"{g['Date']}: {g['PTS']}pts/{g['REB']}reb/{g['AST']}ast" for g in games])
                        )
                    else:
                        stats_text = (
                            f"{sports_stats['team']} last {len(games)} games: " +
                            ", ".join([f"{g['Date']}: {g.get('Score','?')} ({g.get('W/L','?')})" for g in games])
                        )
                import datetime as _dt
                today_str = _dt.date.today().strftime("%B %d, %Y")
                research     = generate_market_research(
                    market_title         = row["event_ticker"],
                    current_price        = row["current_price"],
                    category             = row["category"],
                    edge_score           = edge,
                    price_change_pct     = row["price_change_pct"],
                    news_headlines       = news,
                    today_date           = today_str,
                    player_stats_summary = stats_text,
                )

            # Surface API errors visibly instead of silently failing
            if research and research.get("_error"):
                st.error(f"⚠️ AI verdict failed: {research['_error']}")
                research = None

            # Store in session state so tab doesn't switch on rerender
            st.session_state["research_card"]  = render_research_card(row, research, news, edge, df_markets)
            st.session_state["research_sports"] = render_stats_card(sports_stats) if sports_stats else ""

        # Render from session state — persists without jumping tabs
        if "research_card" in st.session_state:
            st.markdown(st.session_state["research_card"], unsafe_allow_html=True)
            if st.session_state.get("research_sports"):
                st.markdown(st.session_state["research_sports"], unsafe_allow_html=True)
            if st.button("Clear research", key="clear_research"):
                del st.session_state["research_card"]
                del st.session_state["research_sports"]

    else:
        if search_query.strip():
            st.info(f"No markets found for '{search_query}'. Try a broader term.")
        else:
            st.info("Enter a search term above to find markets, or browse by category.")

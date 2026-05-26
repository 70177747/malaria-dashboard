from pathlib import Path
import re
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(
    page_title="Pakistan Malaria Premium Dashboard",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent / "data"
INCIDENCE_FILE = DATA_DIR / "442CEA8_ALL_LATEST.csv"
MORTALITY_FILE = DATA_DIR / "GHE_FULL_DD(1).csv"

THEMES = {
    "Emerald Dark": {
        "bg1": "#06131f", "bg2": "#0f2f2d", "card": "rgba(15,23,42,.78)",
        "accent": "#2dd4bf", "accent2": "#38bdf8", "text": "#f8fafc", "muted": "#a7b7c7",
        "template": "plotly_dark", "palette": ["#2dd4bf", "#38bdf8", "#a78bfa", "#f59e0b", "#fb7185", "#84cc16"]
    },
    "Royal Blue": {
        "bg1": "#071022", "bg2": "#111b4d", "card": "rgba(15,23,42,.82)",
        "accent": "#60a5fa", "accent2": "#c084fc", "text": "#f8fafc", "muted": "#b7c4d6",
        "template": "plotly_dark", "palette": ["#60a5fa", "#c084fc", "#22d3ee", "#f97316", "#f472b6", "#34d399"]
    },
    "Clean Light": {
        "bg1": "#f8fafc", "bg2": "#e0f2fe", "card": "rgba(255,255,255,.86)",
        "accent": "#0284c7", "accent2": "#059669", "text": "#0f172a", "muted": "#475569",
        "template": "plotly_white", "palette": ["#0284c7", "#059669", "#7c3aed", "#ea580c", "#e11d48", "#65a30d"]
    },
}

@st.cache_data(show_spinner="Loading and cleaning WHO malaria dataset...")
def load_data():
    inc = pd.read_csv(INCIDENCE_FILE)
    mort = pd.read_csv(MORTALITY_FILE)
    inc.columns = inc.columns.str.strip()
    mort.columns = mort.columns.str.strip()

    numeric_inc = ["DIM_TIME", "RATE_PER_1000_N", "RATE_PER_1000_NL", "RATE_PER_1000_NU"]
    for col in numeric_inc:
        if col in inc.columns:
            inc[col] = pd.to_numeric(inc[col], errors="coerce")

    for col in ["DIM_YEAR_CODE", "VAL_DTHS_RATE100K_NUMERIC"]:
        if col in mort.columns:
            mort[col] = pd.to_numeric(mort[col], errors="coerce")

    inc = inc.dropna(subset=["DIM_TIME", "RATE_PER_1000_N"]).copy()
    inc["DIM_TIME"] = inc["DIM_TIME"].astype(int)
    inc["Search_Text"] = (inc["GEO_NAME_SHORT"].astype(str) + " " + inc["IND_NAME"].astype(str)).str.lower()

    mort = mort.dropna(subset=["DIM_YEAR_CODE", "VAL_DTHS_RATE100K_NUMERIC"]).copy()
    mort["DIM_YEAR_CODE"] = mort["DIM_YEAR_CODE"].astype(int)
    return inc, mort

incidence, mortality = load_data()

with st.sidebar:
    theme_name = st.selectbox("🎨 Dashboard Theme", list(THEMES.keys()), index=0)
T = THEMES[theme_name]

st.markdown(f"""
<style>
:root {{ --accent:{T['accent']}; --accent2:{T['accent2']}; --text:{T['text']}; --muted:{T['muted']}; }}
.stApp {{ background: radial-gradient(circle at top left, {T['bg2']} 0%, {T['bg1']} 42%, {T['bg1']} 100%); color:var(--text); }}
.block-container {{ padding: 1rem 1.3rem 3rem; max-width: 1500px; }}
[data-testid="stSidebar"] {{ background: linear-gradient(180deg, rgba(2,6,23,.96), rgba(15,23,42,.94)); border-right:1px solid rgba(148,163,184,.22); }}
[data-testid="stMetricValue"] {{ color: var(--text); }}
.hero {{ padding: clamp(18px,3vw,34px); border-radius: 30px; background: linear-gradient(135deg, rgba(45,212,191,.20), rgba(56,189,248,.12)); border:1px solid rgba(148,163,184,.24); box-shadow:0 22px 60px rgba(0,0,0,.23); }}
.hero h1 {{ font-size: clamp(30px,5vw,58px); line-height:1.02; margin:0; color:var(--text); letter-spacing:-1.2px; }}
.hero p {{ font-size: clamp(14px,2vw,17px); color:var(--muted); margin:12px 0 0; max-width:900px; }}
.pill {{ display:inline-block; padding:7px 12px; margin-bottom:14px; border-radius:999px; background:rgba(45,212,191,.12); border:1px solid rgba(45,212,191,.28); color:var(--accent); font-weight:700; font-size:13px; }}
.metric-card {{ min-height:112px; padding:18px 18px; border-radius:24px; background:{T['card']}; border:1px solid rgba(148,163,184,.22); box-shadow:0 16px 40px rgba(0,0,0,.18); }}
.metric-card .label {{ color:var(--muted); font-size:13px; }}
.metric-card .value {{ color:var(--text); font-weight:900; font-size:clamp(24px,3vw,34px); margin-top:4px; }}
.metric-card .note {{ color:var(--accent2); font-size:12px; margin-top:4px; }}
.chart-card {{ background:{T['card']}; border:1px solid rgba(148,163,184,.18); border-radius:24px; padding:10px 10px 0; margin-bottom:16px; }}
.section-title {{ font-size:clamp(22px,3vw,30px); font-weight:900; margin:28px 0 10px; color:var(--text); }}
.small-muted {{ color:var(--muted); font-size:13px; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 10px; flex-wrap: wrap; }}
.stTabs [data-baseweb="tab"] {{ border-radius:999px; padding:10px 16px; background:rgba(148,163,184,.12); }}
@media (max-width: 768px) {{
  .block-container {{ padding-left:.7rem; padding-right:.7rem; }}
  .hero {{ border-radius:22px; }}
  .metric-card {{ margin-bottom:10px; }}
}}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🦟 Control Panel")
    st.caption("Every filter updates every chart instantly.")
    years = sorted(incidence["DIM_TIME"].dropna().unique().tolist())
    year_range = st.slider("Year / Time Range", int(min(years)), int(max(years)), (int(min(years)), int(max(years))))

    countries = sorted(incidence["GEO_NAME_SHORT"].dropna().unique().tolist())
    default_countries = ["Pakistan"] if "Pakistan" in countries else countries[:3]
    selected_countries = st.multiselect("Country / Region", countries, default=default_countries)

    indicators = sorted(incidence["IND_NAME"].dropna().unique().tolist())
    selected_indicators = st.multiselect("Indicator", indicators, default=indicators[:1])

    rate_min, rate_max = float(incidence["RATE_PER_1000_N"].min()), float(incidence["RATE_PER_1000_N"].max())
    rate_range = st.slider("Numerical Range: Rate per 1,000", rate_min, rate_max, (rate_min, rate_max))

    search = st.text_input("Search / Text Filter", placeholder="Pakistan, malaria cases...")
    sex_options = sorted(mortality["DIM_SEX_CODE"].dropna().unique().tolist())
    selected_sex = st.multiselect("Mortality Sex Category", sex_options, default=sex_options)
    show_table = st.toggle("Show raw data table", value=True)
    if st.button("🔄 Reset / Clear Filters", use_container_width=True):
        st.rerun()

f = incidence[
    incidence["DIM_TIME"].between(year_range[0], year_range[1]) &
    incidence["RATE_PER_1000_N"].between(rate_range[0], rate_range[1])
].copy()
if selected_countries:
    f = f[f["GEO_NAME_SHORT"].isin(selected_countries)]
if selected_indicators:
    f = f[f["IND_NAME"].isin(selected_indicators)]
if search:
    words = [w.lower() for w in re.split(r"\s+", search.strip()) if w]
    for w in words:
        f = f[f["Search_Text"].str.contains(re.escape(w), na=False)]

mf = mortality[mortality["DIM_YEAR_CODE"].between(year_range[0], year_range[1])].copy()
if selected_sex:
    mf = mf[mf["DIM_SEX_CODE"].isin(selected_sex)]

st.markdown("""
<div class='hero'>
  <div class='pill'>Premium Streamlit • Interactive EDA • WHO Malaria Dataset</div>
  <h1>Pakistan Malaria Intelligence Dashboard</h1>
  <p>Modern, responsive and presentation-ready dashboard with KPI cards, linked filters, required chart types, clean theme switching, downloadable filtered data and professional insights.</p>
</div>
""", unsafe_allow_html=True)

avg_rate = f["RATE_PER_1000_N"].mean() if not f.empty else 0
max_rate = f["RATE_PER_1000_N"].max() if not f.empty else 0
min_rate = f["RATE_PER_1000_N"].min() if not f.empty else 0
latest_year = f["DIM_TIME"].max() if not f.empty else "—"

st.write("")
c1, c2, c3, c4 = st.columns(4)
metrics = [
    ("Total Records", f"{len(f):,}", "filtered rows"),
    ("Average Rate", f"{avg_rate:,.2f}", "per 1,000 population"),
    ("Highest Rate", f"{max_rate:,.2f}", "maximum signal"),
    ("Latest Year", f"{latest_year}", "current filter endpoint"),
]
for col, (label, value, note) in zip([c1, c2, c3, c4], metrics):
    col.markdown(f"<div class='metric-card'><div class='label'>{label}</div><div class='value'>{value}</div><div class='note'>{note}</div></div>", unsafe_allow_html=True)

if f.empty:
    st.warning("No data found for the selected filters. Please clear or adjust filters.")
    st.stop()

color_seq = T["palette"]
layout_common = dict(template=T["template"], paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(size=13), margin=dict(l=20,r=20,t=60,b=30))

def polish(fig, height=430):
    fig.update_layout(**layout_common, height=height, colorway=color_seq, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148,163,184,.16)", title_font=dict(size=13))
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148,163,184,.16)", title_font=dict(size=13))
    return fig

tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🌍 Compare", "🧪 Statistics", "📋 Data & Insights"])

with tab1:
    st.markdown("<div class='section-title'>Core Malaria Trends</div>", unsafe_allow_html=True)
    trend = f.groupby("DIM_TIME", as_index=False).agg(avg_rate=("RATE_PER_1000_N", "mean"), lower=("RATE_PER_1000_NL", "mean"), upper=("RATE_PER_1000_NU", "mean"))
    a, b = st.columns(2)
    with a:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend["DIM_TIME"], y=trend["upper"], line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=trend["DIM_TIME"], y=trend["lower"], fill="tonexty", line=dict(width=0), name="Uncertainty band", opacity=.25))
        fig.add_trace(go.Scatter(x=trend["DIM_TIME"], y=trend["avg_rate"], mode="lines+markers", name="Average rate"))
        fig.update_layout(title="Line Chart: Average Malaria Incidence Trend")
        st.plotly_chart(polish(fig), use_container_width=True)
    with b:
        fig = px.area(trend, x="DIM_TIME", y="avg_rate", title="Area Chart: Cumulative Visual Trend", color_discrete_sequence=color_seq)
        st.plotly_chart(polish(fig), use_container_width=True)

    if not mf.empty:
        cause = mf.groupby("DIM_GHECAUSE_TITLE", as_index=False)["VAL_DTHS_RATE100K_NUMERIC"].mean().sort_values("VAL_DTHS_RATE100K_NUMERIC", ascending=False).head(12)
        fig = px.bar(cause, x="VAL_DTHS_RATE100K_NUMERIC", y="DIM_GHECAUSE_TITLE", orientation="h", title="Supporting Mortality Signal: Average Death Rate per 100k", color="VAL_DTHS_RATE100K_NUMERIC", color_continuous_scale="Teal")
        fig.update_layout(yaxis={"categoryorder":"total ascending"}, coloraxis_showscale=False)
        st.plotly_chart(polish(fig, 480), use_container_width=True)

with tab2:
    st.markdown("<div class='section-title'>Comparison & Distribution</div>", unsafe_allow_html=True)
    top = f.groupby("GEO_NAME_SHORT", as_index=False)["RATE_PER_1000_N"].mean().sort_values("RATE_PER_1000_N", ascending=False).head(15)
    a, b = st.columns(2)
    with a:
        fig = px.bar(top, x="RATE_PER_1000_N", y="GEO_NAME_SHORT", orientation="h", title="Bar Chart: Top Countries/Regions by Average Rate", color="RATE_PER_1000_N", color_continuous_scale="Viridis")
        fig.update_layout(yaxis={"categoryorder":"total ascending"}, coloraxis_showscale=False)
        st.plotly_chart(polish(fig), use_container_width=True)
    with b:
        fig = px.pie(top, values="RATE_PER_1000_N", names="GEO_NAME_SHORT", hole=.52, title="Pie Chart: Proportional Distribution", color_discrete_sequence=color_seq)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(**layout_common, height=430)
        st.plotly_chart(fig, use_container_width=True)

    a, b = st.columns(2)
    with a:
        fig = px.histogram(f, x="RATE_PER_1000_N", nbins=35, title="Histogram: Frequency Distribution of Incidence Rate", color_discrete_sequence=[T["accent"]])
        st.plotly_chart(polish(fig), use_container_width=True)
    with b:
        fig = px.scatter(f, x="DIM_TIME", y="RATE_PER_1000_N", color="GEO_NAME_SHORT", size="RATE_PER_1000_N", hover_data=["IND_NAME"], title="Scatter Plot: Year vs Rate Relationship", color_discrete_sequence=color_seq)
        st.plotly_chart(polish(fig), use_container_width=True)

with tab3:
    st.markdown("<div class='section-title'>Statistical Quality Views</div>", unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        fig = px.box(f, x="GEO_NAME_SHORT", y="RATE_PER_1000_N", points="outliers", title="Box Plot: Spread, Median & Outliers", color="GEO_NAME_SHORT", color_discrete_sequence=color_seq)
        fig.update_layout(showlegend=False, xaxis_tickangle=-30)
        st.plotly_chart(polish(fig), use_container_width=True)
    with b:
        fig = px.violin(f, x="GEO_NAME_SHORT", y="RATE_PER_1000_N", box=True, points="outliers", title="Violin Plot: Distribution and Density", color="GEO_NAME_SHORT", color_discrete_sequence=color_seq)
        fig.update_layout(showlegend=False, xaxis_tickangle=-30)
        st.plotly_chart(polish(fig), use_container_width=True)

    a, b = st.columns(2)
    with a:
        count_data = f["GEO_NAME_SHORT"].value_counts().head(15).reset_index()
        count_data.columns = ["GEO_NAME_SHORT", "Count"]
        fig = px.bar(count_data, x="GEO_NAME_SHORT", y="Count", title="Count Plot: Frequency Count by Country/Region", color="Count", color_continuous_scale="Teal")
        fig.update_layout(xaxis_tickangle=-30, coloraxis_showscale=False)
        st.plotly_chart(polish(fig), use_container_width=True)
    with b:
        corr_cols = [c for c in ["DIM_TIME", "RATE_PER_1000_N", "RATE_PER_1000_NL", "RATE_PER_1000_NU"] if c in f.columns]
        corr = f[corr_cols].corr(numeric_only=True)
        fig = px.imshow(corr, text_auto=True, title="Heatmap: Correlation Matrix", aspect="auto", color_continuous_scale="Teal")
        fig.update_layout(**layout_common, height=430)
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.markdown("<div class='section-title'>Insights & Dataset Preview</div>", unsafe_allow_html=True)
    highest_row = f.loc[f["RATE_PER_1000_N"].idxmax()]
    st.info(f"Highest filtered incidence appears in **{highest_row['GEO_NAME_SHORT']}** during **{int(highest_row['DIM_TIME'])}** with rate **{highest_row['RATE_PER_1000_N']:.2f} per 1,000**. Average filtered rate is **{avg_rate:.2f}**.")
    csv = f.drop(columns=["Search_Text"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Filtered CSV", csv, "filtered_malaria_dashboard_data.csv", "text/csv", use_container_width=True)
    if show_table:
        st.dataframe(f.drop(columns=["Search_Text"], errors="ignore").head(700), use_container_width=True, hide_index=True)

st.caption("Built with Pandas, NumPy, Matplotlib, Seaborn, Plotly and Streamlit. Dataset filenames are preserved exactly inside the data folder.")

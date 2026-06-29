# =============================================================================
#  Home.py  —  Landing page for Market Analyser Suite
#  Run with:  streamlit run Home.py
# =============================================================================

import streamlit as st

st.set_page_config(
    page_title="Market Analyser Suite",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
body, .main { background-color: #0e1117; }
.app-card {
    background: #1a1f2e;
    border-radius: 14px;
    padding: 28px 32px;
    margin-bottom: 18px;
    border: 1px solid #2a3040;
}
.tag {
    display: inline-block;
    background: #2a3040;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 12px;
    color: #9e9e9e;
    margin: 4px 4px 0 0;
}
.hero-sub { color: #9e9e9e; font-size: 15px; margin-top: -8px; }
</style>
""", unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────────────────
st.title("📊 Market Analyser Suite")
st.markdown('<p class="hero-sub">Benjamin Cowen–inspired macro framework · 200-day MA as core signal</p>',
            unsafe_allow_html=True)
st.divider()

# ── App cards ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-card">
    <h3 style="margin-top:0">₿ Bitcoin &amp; Crypto Analyser</h3>
    <p style="color:#c0c0c0; margin-bottom:12px">
        Live price with 200 MA structure label, whale transaction feed,
        on-chain network signals (fees, mempool, hashrate), and a live
        order-book liquidity heatmap pulled directly from Binance.
    </p>
    <span class="tag">yfinance</span>
    <span class="tag">Binance API (no key)</span>
    <span class="tag">Mempool.space (no key)</span>
    <span class="tag">Whale Alert API (free key)</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-card">
    <h3 style="margin-top:0">📈 Stock Market Analyser</h3>
    <p style="color:#c0c0c0; margin-bottom:12px">
        Live price with 200 MA structure label, SEC EDGAR insider buying/selling,
        institutional holders, options flow with Put/Call ratio and Max Pain,
        short interest data, and live news sentiment scoring.
    </p>
    <span class="tag">yfinance</span>
    <span class="tag">SEC EDGAR (no key)</span>
    <span class="tag">Options Chain (no key)</span>
    <span class="tag">NewsAPI (free key)</span>
</div>
""", unsafe_allow_html=True)

st.info("👈 Use the sidebar to switch between apps.", icon="💡")

# ── Framework explainer ────────────────────────────────────────────────────────
st.divider()
with st.expander("📖 The Framework — Benjamin Cowen 200 MA Logic"):
    st.markdown("""
| Position | Interpretation |
|---|---|
| Price **above** 200 MA | Bull market structure — dips are opportunities |
| Price **below** 200 MA | Zone of interest — accumulate cautiously, wait for reclaim |
| Price **reclaims** 200 MA | Strongest confirmation — historically explosive |
| 200-**week** MA (BTC) | The ultimate long-term floor |

> *"We don't predict. We react to probabilities."* — Benjamin Cowen

The 200-day Moving Average is the single most important macro line on any chart.
Most assets do not stay below it permanently. When they dip below, that is not an
automatic buy — it is a **zone of interest**. You wait for confirmation of reclaim,
and you size accordingly.
    """)

# ── Stack ──────────────────────────────────────────────────────────────────────
st.divider()
st.caption("**Stack:** Python · Streamlit · yfinance · Plotly · pandas · ta-lib · requests")
st.caption("*For portfolio / educational use only. Not financial advice.*")

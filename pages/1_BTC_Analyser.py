# =============================================================================
#  pages/1_BTC_Analyser.py  —  Bitcoin & Crypto Analyser
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime

# Must import from utils (works when run via `streamlit run Home.py`)
from utils.helpers import (
    fetch_ohlcv, add_indicators, ma200_status,
    build_price_chart, build_volatility_chart,
    BG_COLOR, BULL_COLOR, BEAR_COLOR, MA200_COLOR,
    GRID_COLOR, TEXT_COLOR, SHARED_CSS, get_plotly_layout,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BTC Analyser",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(SHARED_CSS, unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("₿ BTC Analyser")
    st.caption("Benjamin Cowen–style macro framework")
    st.divider()

    ticker  = st.selectbox("Asset", ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD"], index=0)
    period  = st.selectbox("Lookback", ["6mo", "1y", "2y", "5y"], index=1)
    whale_min_usd   = st.number_input("Whale tx minimum (USD)", value=1_000_000, step=500_000, min_value=100_000)
    ob_depth        = st.slider("Order book depth (levels)", 20, 100, 50)
    whale_api_key   = st.text_input("Whale Alert API key (free @ whale-alert.io)",
                                    type="password", placeholder="Paste key here — optional")
    st.divider()
    st.caption("Binance & Mempool.space need no API key.")


# ── Load & cache price data ────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_price(ticker, period):
    df = fetch_ohlcv(ticker, period=period)
    if not df.empty:
        df = add_indicators(df)
    return df

with st.spinner("Loading price data…"):
    df = load_price(ticker, period)

if df.empty:
    st.error("Could not load price data. Check your internet connection.")
    st.stop()


# ── Helper: safe float ─────────────────────────────────────────────────────────
def sf(val):
    """Safely convert a potentially multi-dimensional pandas value to float."""
    if hasattr(val, "squeeze"):
        val = val.squeeze()
    if hasattr(val, "item"):
        return float(val.item())
    return float(val)


# ── Header metrics ─────────────────────────────────────────────────────────────
st.title(f"{'Bitcoin' if 'BTC' in ticker else ticker.replace('-USD','')} Market Dashboard")

latest  = df.iloc[-1]
prev    = df.iloc[-2]
price   = sf(latest["Close"])
prev_px = sf(prev["Close"])
chg_pct = ((price - prev_px) / prev_px) * 100
status  = ma200_status(df)
vol     = sf(latest["Volatility"]) if not pd.isna(latest["Volatility"]) else 0.0
rsi     = sf(latest["RSI"])        if not pd.isna(latest["RSI"])        else 0.0
ma200   = sf(latest["MA200"])      if not pd.isna(latest["MA200"])      else 0.0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Price",        f"${price:,.2f}",    f"{chg_pct:+.2f}%")
c2.metric("200 MA",       f"${ma200:,.2f}",    f"{status['pct']:+.1f}%" if status['pct'] else "")
c3.metric("RSI (14)",     f"{rsi:.1f}",
          "Overbought ⚠️" if rsi > 70 else ("Oversold 💡" if rsi < 30 else "Neutral"))
c4.metric("Volatility",   f"{vol:.1f}%",       "30d annualised")
c5.metric("Regime",       "Bull 🟢" if "Bull" in status["label"] else "Bear 🔴", "200 MA signal")

# Macro banner
pct_abs  = abs(status["pct"])
above    = status["pct"] > 0
commentary = (
    "Historically, price holding above the 200 MA confirms long-term bull market structure. "
    "Pullbacks to the 200 MA are high-probability entry zones."
    if above else
    "Historically, price below the 200 MA is a zone of interest — NOT a guaranteed bottom. "
    "Dollar-cost average, stay patient, and wait for a confirmed reclaim before going aggressive."
)
st.markdown(
    f'<div class="metric-card" style="border-color:{status["color"]}">'
    f'<span style="color:{status["color"]}; font-weight:700">{status["label"]}</span><br>'
    f'<span style="color:#9e9e9e; font-size:13px">'
    f'Price is <b>{pct_abs:.1f}%</b> {"above" if above else "below"} the 200 MA. {commentary}'
    f'</span></div>',
    unsafe_allow_html=True,
)


# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈  Price & 200 MA",
    "🐋  Whale Activity",
    "⛓️  On-Chain Signals",
    "📊  Order Book / Liquidity",
])


# ==============================================================================
# TAB 1 — Price & 200 MA
# ==============================================================================
with tab1:
    st.plotly_chart(build_price_chart(df, ticker), use_container_width=True)
    st.plotly_chart(build_volatility_chart(df, ticker), use_container_width=True)

    with st.expander("📖 Benjamin Cowen 200 MA Framework"):
        st.markdown("""
**The 200-day Moving Average is the single most important macro line on any chart.**

| Condition | Signal |
|---|---|
| Price **above** 200 MA | Bull structure — dips are opportunities |
| Price **below** 200 MA | Bear territory — zone of interest, not automatic buy |
| Price **reclaims** 200 MA | Strongest confirmation — historically explosive moves follow |
| **200-week MA** (BTC) | The ultimate long-term floor — never permanently broken |

**How to use it:**
- Below the 200 MA → start a DCA position in tranches
- Wait for a weekly close back above → that's your confirmation
- Above the 200 MA → stay long, use 50 MA as trailing guide

> *"We don't predict. We react to probabilities."* — Benjamin Cowen
        """)


# ==============================================================================
# TAB 2 — Whale Activity
# ==============================================================================
with tab2:
    st.subheader("🐋 Large Transaction Feed")
    st.caption("Powered by Whale Alert API. Moving BTC **to** exchanges = sell signal. Moving **away** = accumulation.")

    if not whale_api_key:
        st.info(
            "🔑 Paste your **free** Whale Alert API key in the sidebar to enable live whale tracking.  \n"
            "Get one at [whale-alert.io](https://whale-alert.io) — the free plan is enough for this app.",
            icon="💡",
        )
        # Demo preview
        st.caption("Preview — this is what the feed looks like with a key:")
        demo = pd.DataFrame([
            {"Time":"2024-06-01 08:32","Symbol":"BTC","Amount":"1,240.00",
             "USD Value":"$52,400,000","From":"unknown wallet","To":"Binance","Signal":"🔴 Sell pressure (to exchange)"},
            {"Time":"2024-06-01 07:11","Symbol":"BTC","Amount":"890.00",
             "USD Value":"$37,600,000","From":"Coinbase","To":"unknown wallet","Signal":"🟢 Accumulation (from exchange)"},
            {"Time":"2024-06-01 06:45","Symbol":"BTC","Amount":"2,100.00",
             "USD Value":"$88,700,000","From":"unknown wallet","To":"unknown wallet","Signal":"⚪ Wallet move (watch)"},
            {"Time":"2024-06-01 05:30","Symbol":"ETH","Amount":"12,000.00",
             "USD Value":"$43,200,000","From":"unknown wallet","To":"Kraken","Signal":"🔴 Sell pressure (to exchange)"},
        ])
        st.dataframe(demo, use_container_width=True, hide_index=True)
    else:
        @st.cache_data(ttl=120)
        def fetch_whale_txns(api_key, min_usd):
            url    = "https://api.whale-alert.io/v1/transactions"
            params = {"api_key": api_key, "min_value": int(min_usd), "limit": 100}
            try:
                r = requests.get(url, params=params, timeout=10)
                if r.status_code == 200:
                    return r.json().get("transactions", [])
                st.warning(f"Whale Alert API returned status {r.status_code}: {r.text[:200]}")
            except Exception as e:
                st.error(f"Request failed: {e}")
            return []

        with st.spinner("Fetching whale transactions…"):
            txns = fetch_whale_txns(whale_api_key, whale_min_usd)

        if txns:
            def whale_signal(from_type, to_type):
                f, t = from_type.lower(), to_type.lower()
                if "exchange" in t and "exchange" not in f:
                    return "🔴 Sell pressure (to exchange)"
                elif "exchange" in f and "exchange" not in t:
                    return "🟢 Accumulation (from exchange)"
                elif "miner" in f:
                    return "⛏️ Miner outflow"
                return "⚪ Wallet movement (watch)"

            rows = []
            for t in txns:
                from_info = t.get("from", {})
                to_info   = t.get("to",   {})
                rows.append({
                    "Time":      datetime.utcfromtimestamp(t.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M"),
                    "Symbol":    t.get("symbol", "").upper(),
                    "Amount":    f"{t.get('amount', 0):,.2f}",
                    "USD Value": f"${t.get('amount_usd', 0):,.0f}",
                    "From":      from_info.get("owner", from_info.get("owner_type", "unknown")),
                    "To":        to_info.get("owner",   to_info.get("owner_type",   "unknown")),
                    "Signal":    whale_signal(
                        from_info.get("owner_type", ""),
                        to_info.get("owner_type",   ""),
                    ),
                })

            wdf       = pd.DataFrame(rows)
            n_sell    = (wdf["Signal"].str.contains("Sell")).sum()
            n_accum   = (wdf["Signal"].str.contains("Accum")).sum()
            n_miner   = (wdf["Signal"].str.contains("Miner")).sum()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Transactions", len(wdf))
            col2.metric("🔴 To Exchange",     int(n_sell))
            col3.metric("🟢 From Exchange",   int(n_accum))
            col4.metric("⛏️ Miner Outflow",   int(n_miner))

            if n_accum > n_sell:
                st.success("🟢 Net whale flow is **away** from exchanges — accumulation signal.")
            elif n_sell > n_accum:
                st.warning("🔴 Net whale flow is **toward** exchanges — potential sell pressure.")

            st.dataframe(wdf, use_container_width=True, hide_index=True)

            if st.button("🔄 Refresh Whale Feed"):
                st.cache_data.clear()
                st.rerun()
        else:
            st.warning("No transactions found. Try lowering the minimum USD threshold in the sidebar.")


# ==============================================================================
# TAB 3 — On-Chain Signals
# ==============================================================================
with tab3:
    st.subheader("⛓️ On-Chain Signals via Mempool.space")
    st.caption("No API key required. Data refreshes every 5 minutes.")

    @st.cache_data(ttl=300)
    def fetch_mempool():
        result = {}
        endpoints = {
            "fees":     "https://mempool.space/api/v1/fees/recommended",
            "mempool":  "https://mempool.space/api/mempool",
            "hashrate": "https://mempool.space/api/v1/mining/hashrate/3m",
            "blocks":   "https://mempool.space/api/v1/blocks",
        }
        for key, url in endpoints.items():
            try:
                r = requests.get(url, timeout=8)
                if r.status_code == 200:
                    result[key] = r.json()
            except Exception:
                pass
        return result

    with st.spinner("Fetching on-chain data…"):
        onchain = fetch_mempool()

    if not onchain:
        st.error("Could not reach Mempool.space. Check your internet connection.")
    else:
        # ── Fees ──
        st.markdown("#### ⛽ Network Fee Environment")
        if "fees" in onchain:
            fees = onchain["fees"]
            f1, f2, f3, f4 = st.columns(4)
            f1.metric("Next Block (fast)",  f"{fees.get('fastestFee',  '?')} sat/vB")
            f2.metric("~30 min",            f"{fees.get('halfHourFee', '?')} sat/vB")
            f3.metric("~1 hour",            f"{fees.get('hourFee',     '?')} sat/vB")
            f4.metric("Min Fee",            f"{fees.get('minimumFee',  '?')} sat/vB")

            fastest = fees.get("fastestFee", 0)
            if fastest > 100:
                st.error("🔥 Very high fees — network is heavily congested. Often signals peak demand / bull phase.")
            elif fastest > 30:
                st.warning("📊 Moderate fees — normal activity levels.")
            else:
                st.success("💤 Low fees — quiet network. Can signal accumulation or low speculative activity.")
        st.divider()

        # ── Mempool ──
        st.markdown("#### 🗂️ Mempool Status")
        if "mempool" in onchain:
            mem = onchain["mempool"]
            m1, m2, m3 = st.columns(3)
            m1.metric("Pending Transactions", f"{mem.get('count', 0):,}")
            m2.metric("Mempool Size",          f"{mem.get('vsize', 0) / 1e6:.1f} MB")
            m3.metric("Total Fees (BTC)",      f"{mem.get('total_fee', 0) / 1e8:.4f}" if "total_fee" in mem else "—")

            count = mem.get("count", 0)
            if count > 100_000:
                st.warning("📦 Very large mempool — extreme demand for block space.")
            elif count > 30_000:
                st.info("📦 Elevated mempool — moderate congestion.")
            else:
                st.success("✅ Mempool is clear — low congestion.")
        st.divider()

        # ── Hashrate ──
        st.markdown("#### ⚡ Network Hashrate (3 months)")
        if "hashrate" in onchain:
            hr_list = onchain["hashrate"].get("hashrates", [])
            if hr_list:
                hr_df = pd.DataFrame(hr_list)
                hr_df["timestamp"] = pd.to_datetime(hr_df["timestamp"], unit="s")
                hr_df["hashrate_eh"] = hr_df["avgHashrate"] / 1e18

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=hr_df["timestamp"],
                    y=hr_df["hashrate_eh"],
                    fill="tozeroy",
                    line=dict(color=MA200_COLOR, width=2),
                    fillcolor="rgba(245,166,35,0.12)",
                    name="Hashrate (EH/s)",
                ))
                fig.update_layout(**get_plotly_layout("Bitcoin Network Hashrate (EH/s)", height=300))
                st.plotly_chart(fig, use_container_width=True)

                latest_hr = hr_df["hashrate_eh"].iloc[-1]
                prev_hr   = hr_df["hashrate_eh"].iloc[-30] if len(hr_df) > 30 else hr_df["hashrate_eh"].iloc[0]
                hr_chg    = ((latest_hr - prev_hr) / prev_hr) * 100

                col1, col2 = st.columns(2)
                col1.metric("Current Hashrate", f"{latest_hr:.1f} EH/s")
                col2.metric("30-day Change",     f"{hr_chg:+.1f}%",
                            "Bullish 🟢" if hr_chg > 0 else "Miner caution 🔴")

                st.caption(
                    "📖 **Rising hashrate** = miners profitable & confident → long-term bullish signal.  "
                    "**Dropping hashrate** = miner capitulation → historically marks cycle bottoms."
                )

        if st.button("🔄 Refresh On-Chain Data"):
            st.cache_data.clear()
            st.rerun()


# ==============================================================================
# TAB 4 — Order Book / Liquidity Heatmap
# ==============================================================================
with tab4:
    st.subheader("📊 Live Order Book — Liquidity Heatmap")
    st.caption("Real-time bid/ask depth from Binance public API. No API key required.")

    symbol_map = {"BTC-USD": "BTCUSDT", "ETH-USD": "ETHUSDT",
                  "SOL-USD": "SOLUSDT", "BNB-USD": "BNBUSDT"}
    binance_symbol = symbol_map.get(ticker, "BTCUSDT")

    @st.cache_data(ttl=15)
    def fetch_orderbook(symbol, limit):
        url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit={limit}"
        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    with st.spinner("Fetching live order book from Binance…"):
        ob = fetch_orderbook(binance_symbol, ob_depth)

    if not ob:
        st.error("Could not reach Binance API. Check your connection.")
    else:
        bids = pd.DataFrame(ob["bids"], columns=["price", "qty"], dtype=float)
        asks = pd.DataFrame(ob["asks"], columns=["price", "qty"], dtype=float)

        bids.sort_values("price", ascending=False, inplace=True)
        asks.sort_values("price", ascending=True,  inplace=True)

        bids["cum_qty"]   = bids["qty"].cumsum()
        asks["cum_qty"]   = asks["qty"].cumsum()
        bids["usd_value"] = bids["price"] * bids["qty"]
        asks["usd_value"] = asks["price"] * asks["qty"]

        mid_price = (bids["price"].iloc[0] + asks["price"].iloc[0]) / 2
        spread    = asks["price"].iloc[0] - bids["price"].iloc[0]
        spread_pct = (spread / mid_price) * 100

        # Header metrics
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Mid Price",    f"${mid_price:,.2f}")
        c2.metric("Best Bid",     f"${bids['price'].iloc[0]:,.2f}")
        c3.metric("Best Ask",     f"${asks['price'].iloc[0]:,.2f}")
        c4.metric("Spread",       f"${spread:.2f}",  f"{spread_pct:.3f}%")
        c5.metric("Bid Depth",    f"${bids['usd_value'].sum():,.0f}")

        # Largest walls
        top_bid = bids.nlargest(1, "qty").iloc[0]
        top_ask = asks.nlargest(1, "qty").iloc[0]
        w1, w2  = st.columns(2)
        w1.markdown(
            f'<div class="metric-card" style="border-color:{BULL_COLOR}">'
            f'<b style="color:{BULL_COLOR}">🟢 Largest Buy Wall</b><br>'
            f'<span style="font-size:22px; font-weight:bold">${top_bid["price"]:,.2f}</span><br>'
            f'<span style="color:#9e9e9e">{top_bid["qty"]:.4f} BTC  ·  ${top_bid["usd_value"]:,.0f}</span>'
            f'</div>', unsafe_allow_html=True,
        )
        w2.markdown(
            f'<div class="metric-card" style="border-color:{BEAR_COLOR}">'
            f'<b style="color:{BEAR_COLOR}">🔴 Largest Sell Wall</b><br>'
            f'<span style="font-size:22px; font-weight:bold">${top_ask["price"]:,.2f}</span><br>'
            f'<span style="color:#9e9e9e">{top_ask["qty"]:.4f} BTC  ·  ${top_ask["usd_value"]:,.0f}</span>'
            f'</div>', unsafe_allow_html=True,
        )

        # ── Depth chart ──
        st.markdown("#### 📉 Cumulative Order Book Depth")
        fig_depth = go.Figure()
        fig_depth.add_trace(go.Scatter(
            x=bids["price"], y=bids["cum_qty"],
            fill="tozeroy",
            line=dict(color=BULL_COLOR, width=2),
            fillcolor="rgba(0,200,150,0.15)",
            name="Bids (Buy Liquidity)",
        ))
        fig_depth.add_trace(go.Scatter(
            x=asks["price"], y=asks["cum_qty"],
            fill="tozeroy",
            line=dict(color=BEAR_COLOR, width=2),
            fillcolor="rgba(255,78,106,0.15)",
            name="Asks (Sell Liquidity)",
        ))
        fig_depth.add_vline(
            x=mid_price, line_dash="dash", line_color=MA200_COLOR, line_width=1.5,
            annotation_text=f" Mid ${mid_price:,.0f}",
            annotation_font_color=MA200_COLOR,
        )
        fig_depth.update_layout(**get_plotly_layout(
            f"{binance_symbol} — Cumulative Order Book Depth", height=420))
        st.plotly_chart(fig_depth, use_container_width=True)

        # ── Heatmap (USD liquidity per price level) ──
        st.markdown("#### 🌡️ Liquidity Heatmap — USD Value per Price Level")
        fig_heat = go.Figure()
        fig_heat.add_trace(go.Bar(
            x=bids["price"],
            y=bids["usd_value"],
            marker=dict(
                color=bids["usd_value"],
                colorscale=[[0, "rgba(0,200,150,0.15)"], [1, BULL_COLOR]],
                showscale=False,
            ),
            name="Bid Liquidity (USD)",
        ))
        fig_heat.add_trace(go.Bar(
            x=asks["price"],
            y=asks["usd_value"],
            marker=dict(
                color=asks["usd_value"],
                colorscale=[[0, "rgba(255,78,106,0.15)"], [1, BEAR_COLOR]],
                showscale=False,
            ),
            name="Ask Liquidity (USD)",
        ))
        fig_heat.add_vline(
            x=mid_price, line_dash="dash",
            line_color=MA200_COLOR, line_width=1.5,
        )
        fig_heat.update_layout(**get_plotly_layout(
            "USD Liquidity Distribution by Price Level", height=380))
        st.plotly_chart(fig_heat, use_container_width=True)

        st.caption(
            "📖 **How to read this:**  "
            "Tall green bars = large buy walls — price tends to **bounce** here.  "
            "Tall red bars = large sell walls — price tends to **stall or reverse** here.  "
            "Combined with the 200 MA position, these levels give you high-probability confluence zones."
        )

        if st.button("🔄 Refresh Order Book"):
            st.cache_data.clear()
            st.rerun()

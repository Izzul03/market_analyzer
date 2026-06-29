# =============================================================================
#  pages/2_Stock_Analyser.py  —  Stock Market Analyser
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
import plotly.graph_objects as go

from utils.helpers import (
    fetch_ohlcv, add_indicators, ma200_status,
    build_price_chart, build_volatility_chart,
    BULL_COLOR, BEAR_COLOR, MA200_COLOR, MA50_COLOR,
    GRID_COLOR, TEXT_COLOR, SHARED_CSS, get_plotly_layout,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Analyser",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(SHARED_CSS, unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📈 Stock Analyser")
    st.caption("Institutional-grade signals — free tier")
    st.divider()

    ticker  = st.text_input("Ticker symbol", value="AAPL",
                            placeholder="e.g. AAPL, TSLA, KLSE:1155").upper().strip()
    period  = st.selectbox("Lookback", ["6mo", "1y", "2y", "5y"], index=1)
    news_key = st.text_input("NewsAPI key (free @ newsapi.org)",
                             type="password", placeholder="Optional — for news tab")
    st.divider()
    st.caption("SEC EDGAR & options data need no API key.")


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_price(ticker, period):
    df = fetch_ohlcv(ticker, period=period)
    if not df.empty:
        df = add_indicators(df)
    return df

@st.cache_data(ttl=600)
def load_info(ticker):
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}

with st.spinner("Loading data…"):
    df   = load_price(ticker, period)
    info = load_info(ticker)

if df.empty:
    st.error(f"No data found for **{ticker}**. Check the ticker symbol and try again.")
    st.stop()


# ── Helper ─────────────────────────────────────────────────────────────────────
def sf(val):
    if hasattr(val, "squeeze"): val = val.squeeze()
    if hasattr(val, "item"):    return float(val.item())
    return float(val)


# ── Header ─────────────────────────────────────────────────────────────────────
company = info.get("longName", ticker)
sector  = info.get("sector",   "—")
mktcap  = info.get("marketCap", 0)

st.title(f"{company} ({ticker})")
st.caption(
    f"Sector: **{sector}**  ·  Market Cap: **${mktcap/1e9:.1f}B**"
    if mktcap else f"Sector: {sector}"
)

latest  = df.iloc[-1]
prev    = df.iloc[-2]
price   = sf(latest["Close"])
prev_px = sf(prev["Close"])
chg_pct = ((price - prev_px) / prev_px) * 100
status  = ma200_status(df)
vol     = sf(latest["Volatility"]) if not pd.isna(latest["Volatility"]) else 0.0
rsi     = sf(latest["RSI"])        if not pd.isna(latest["RSI"])        else 0.0
ma200   = sf(latest["MA200"])      if not pd.isna(latest["MA200"])      else 0.0

lo52  = info.get("fiftyTwoWeekLow",  0)
hi52  = info.get("fiftyTwoWeekHigh", 0)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Price",       f"${price:,.2f}",  f"{chg_pct:+.2f}%")
c2.metric("200 MA",      f"${ma200:,.2f}",  f"{status['pct']:+.1f}%")
c3.metric("RSI (14)",    f"{rsi:.1f}",
          "Overbought ⚠️" if rsi > 70 else ("Oversold 💡" if rsi < 30 else "Neutral"))
c4.metric("Volatility",  f"{vol:.1f}%",     "30d annualised")
c5.metric("52w Range",   f"${lo52:.2f} – ${hi52:.2f}" if lo52 else "—", "")

pct_abs = abs(status["pct"])
above   = status["pct"] > 0
st.markdown(
    f'<div class="metric-card" style="border-color:{status["color"]}">'
    f'<span style="color:{status["color"]}; font-weight:700">{status["label"]}</span><br>'
    f'<span style="color:#9e9e9e; font-size:13px">'
    f'Price is <b>{pct_abs:.1f}%</b> {"above" if above else "below"} the 200 MA. '
    f'{"Bull market structure intact — dips to the 200 MA are historically high-probability entries." if above else "Below the 200 MA — zone of interest. Accumulate carefully and wait for a confirmed weekly reclaim before sizing up."}'
    f'</span></div>',
    unsafe_allow_html=True,
)


# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈  Price & 200 MA",
    "🏦  Insider / Institutional",
    "📋  Options Flow",
    "📰  Short Interest & Sentiment",
])


# ==============================================================================
# TAB 1 — Price & 200 MA
# ==============================================================================
with tab1:
    st.plotly_chart(build_price_chart(df, ticker), use_container_width=True)
    st.plotly_chart(build_volatility_chart(df, ticker), use_container_width=True)

    with st.expander("📊 Key Fundamentals"):
        funda = {
            "P/E (TTM)":        info.get("trailingPE"),
            "Forward P/E":      info.get("forwardPE"),
            "EPS (TTM)":        info.get("trailingEps"),
            "Revenue (TTM)":    f"${info.get('totalRevenue', 0)/1e9:.1f}B" if info.get("totalRevenue") else None,
            "Profit Margin":    f"{info.get('profitMargins',0)*100:.1f}%" if info.get("profitMargins") else None,
            "ROE":              f"{info.get('returnOnEquity',0)*100:.1f}%" if info.get("returnOnEquity") else None,
            "Debt / Equity":    f"{info.get('debtToEquity','—')}",
            "Dividend Yield":   f"{info.get('dividendYield',0)*100:.2f}%" if info.get("dividendYield") else None,
            "Beta":             info.get("beta"),
            "Analyst Target":   f"${info.get('targetMeanPrice',0):.2f}" if info.get("targetMeanPrice") else None,
            "Analyst Rating":   info.get("recommendationKey", "—").replace("_", " ").title(),
        }
        valid = {k: v for k, v in funda.items() if v is not None}
        cols  = st.columns(4)
        for i, (k, v) in enumerate(valid.items()):
            cols[i % 4].metric(k, v)


# ==============================================================================
# TAB 2 — Insider / Institutional Activity
# ==============================================================================
with tab2:
    st.subheader("🏦 Insider Transactions — SEC EDGAR (Form 4)")
    st.caption(
        "Insider buying below the 200 MA is one of the strongest confluence signals in all of markets. "
        "They know the business better than anyone."
    )

    @st.cache_data(ttl=3600)
    def get_insider(ticker):
        try:
            df = yf.Ticker(ticker).insider_transactions
            return df if df is not None and not df.empty else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @st.cache_data(ttl=3600)
    def get_institutions(ticker):
        try:
            df = yf.Ticker(ticker).institutional_holders
            return df if df is not None and not df.empty else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @st.cache_data(ttl=3600)
    def get_major_holders(ticker):
        try:
            df = yf.Ticker(ticker).major_holders
            return df if df is not None and not df.empty else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    insider_df = get_insider(ticker)
    inst_df    = get_institutions(ticker)
    major_df   = get_major_holders(ticker)

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("#### Recent Insider Transactions")
        if not insider_df.empty:
            # Detect buy/sell from any column
            def is_buy(row):
                return any("buy" in str(v).lower() or "purchase" in str(v).lower()
                           for v in row.values)
            def is_sell(row):
                return any("sell" in str(v).lower() or "sale" in str(v).lower()
                           for v in row.values)

            n_buy  = insider_df.apply(is_buy,  axis=1).sum()
            n_sell = insider_df.apply(is_sell, axis=1).sum()

            b1, b2, b3 = st.columns(3)
            b1.metric("Total Filings",   len(insider_df))
            b2.metric("🟢 Buys / Purchases", int(n_buy))
            b3.metric("🔴 Sells / Sales",    int(n_sell))

            if n_buy > n_sell:
                st.success(
                    "🟢 Insiders are **net buyers** — historically a strong bullish signal, "
                    "especially when combined with a 200 MA reclaim."
                )
            elif n_sell > n_buy:
                st.warning(
                    "🔴 Insiders are **net sellers** — can reflect diversification or option exercises, "
                    "but worth monitoring alongside the 200 MA position."
                )
            else:
                st.info("⚪ Insider activity is balanced — no clear directional signal.")

            # Show most useful columns
            show_cols = [c for c in
                         ["Insider Trading", "Relationship", "Transaction", "Value", "Shares", "Date Started"]
                         if c in insider_df.columns]
            if not show_cols:
                show_cols = insider_df.columns.tolist()[:6]
            st.dataframe(insider_df[show_cols].head(25),
                         use_container_width=True, hide_index=True)
        else:
            st.info("No insider transaction data returned for this ticker.")

    with col_right:
        st.markdown("#### Top Institutional Holders")
        if not inst_df.empty:
            disp = inst_df.copy()
            # Format % Out column if present
            for col in disp.columns:
                if "%" in col or "pct" in col.lower():
                    disp[col] = disp[col].apply(
                        lambda x: f"{x*100:.2f}%" if isinstance(x, (float, np.floating)) else x
                    )
            st.dataframe(disp.head(15), use_container_width=True, hide_index=True)
        else:
            st.info("No institutional holder data available.")

        if not major_df.empty:
            st.markdown("#### Major Holder Breakdown")
            st.dataframe(major_df, use_container_width=True, hide_index=True)

        with st.expander("📖 Why this matters"):
            st.markdown("""
When large institutions (Vanguard, BlackRock, Fidelity) **increase** their stake, it reflects long-term conviction. Combined with:
- Price **below** 200 MA → Insiders buying = accumulation signal
- Price **above** 200 MA + institutional increase → momentum confirmation

This is the stock market equivalent of whale accumulation in crypto.
            """)


# ==============================================================================
# TAB 3 — Options Flow
# ==============================================================================
with tab3:
    st.subheader("📋 Options Flow — Put/Call Ratio & Max Pain")
    st.caption("Smart money often signals direction through options before price moves. No API key required.")

    @st.cache_data(ttl=600)
    def get_expirations(ticker):
        try:
            return list(yf.Ticker(ticker).options)
        except Exception:
            return []

    @st.cache_data(ttl=600)
    def get_option_chain(ticker, exp):
        try:
            chain = yf.Ticker(ticker).option_chain(exp)
            return chain.calls, chain.puts
        except Exception:
            return None, None

    exps = get_expirations(ticker)

    if not exps:
        st.info(f"No options data available for **{ticker}**. Options are only available for US-listed stocks.")
    else:
        exp_sel = st.selectbox("Expiration date", exps[:12])
        calls, puts = get_option_chain(ticker, exp_sel)

        if calls is not None and puts is not None:
            total_call_oi  = calls["openInterest"].fillna(0).sum()
            total_put_oi   = puts["openInterest"].fillna(0).sum()
            total_call_vol = calls["volume"].fillna(0).sum()
            total_put_vol  = puts["volume"].fillna(0).sum()

            pc_oi  = total_put_oi  / total_call_oi  if total_call_oi  > 0 else 0
            pc_vol = total_put_vol / total_call_vol if total_call_vol > 0 else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Call OI",    f"{int(total_call_oi):,}")
            c2.metric("Total Put OI",     f"{int(total_put_oi):,}")
            c3.metric("P/C Ratio (OI)",   f"{pc_oi:.2f}",
                      "Bearish 🔴" if pc_oi > 1.0 else "Bullish 🟢")
            c4.metric("P/C Ratio (Vol)",  f"{pc_vol:.2f}",
                      "Bearish 🔴" if pc_vol > 1.0 else "Bullish 🟢")

            if pc_oi < 0.7:
                st.success("🟢 Low P/C ratio — heavy call buying. Market is positioned bullishly.")
            elif pc_oi > 1.3:
                st.error("🔴 High P/C ratio — heavy put buying. Bearish sentiment or institutional hedging.")
            else:
                st.info("⚪ Neutral P/C ratio — no strong directional options signal.")

            # ── Max Pain ──
            all_strikes = sorted(set(calls["strike"].tolist() + puts["strike"].tolist()))

            def calc_max_pain(strikes, calls_df, puts_df):
                pain = {}
                for s in strikes:
                    c_pain = ((s - calls_df["strike"]) * calls_df["openInterest"].fillna(0)).clip(lower=0).sum()
                    p_pain = ((puts_df["strike"] - s)  * puts_df["openInterest"].fillna(0)).clip(lower=0).sum()
                    pain[s] = c_pain + p_pain
                return min(pain, key=pain.get) if pain else price

            max_pain_px = calc_max_pain(all_strikes, calls, puts)
            mp_diff     = ((max_pain_px - price) / price) * 100

            st.markdown("---")
            mp1, mp2 = st.columns(2)
            mp1.metric("📍 Max Pain Price",     f"${max_pain_px:,.2f}",
                       f"{mp_diff:+.1f}% from current price")
            mp2.metric("Current Price",          f"${price:,.2f}")
            st.caption(
                "**Max Pain** is the price where the maximum number of options expire worthless. "
                "Market makers are incentivised to pin price near this level into expiry. "
                "Strong gravitational pull, especially in the final week before expiration."
            )

            # ── OI by strike chart ──
            st.markdown("#### Open Interest Distribution by Strike")
            fig_oi = go.Figure()
            fig_oi.add_trace(go.Bar(
                x=calls["strike"], y=calls["openInterest"].fillna(0),
                name="Call OI", marker_color=BULL_COLOR, opacity=0.8,
            ))
            fig_oi.add_trace(go.Bar(
                x=puts["strike"], y=puts["openInterest"].fillna(0),
                name="Put OI", marker_color=BEAR_COLOR, opacity=0.8,
            ))
            fig_oi.add_vline(x=price,        line_dash="dash", line_color=MA200_COLOR,
                             annotation_text=f" Price ${price:.0f}", annotation_font_color=MA200_COLOR)
            fig_oi.add_vline(x=max_pain_px,  line_dash="dot",  line_color="#9e9e9e",
                             annotation_text=f" Max Pain ${max_pain_px:.0f}", annotation_font_color="#9e9e9e")
            fig_oi.update_layout(barmode="overlay", **get_plotly_layout(
                f"Open Interest by Strike — Exp: {exp_sel}", height=400))
            st.plotly_chart(fig_oi, use_container_width=True)

            # ── Top tables ──
            c_left, c_right = st.columns(2)
            with c_left:
                st.markdown("##### 🟢 Top Calls by OI")
                st.dataframe(
                    calls[["strike","lastPrice","openInterest","volume","impliedVolatility"]]
                    .sort_values("openInterest", ascending=False).head(10),
                    use_container_width=True, hide_index=True,
                )
            with c_right:
                st.markdown("##### 🔴 Top Puts by OI")
                st.dataframe(
                    puts[["strike","lastPrice","openInterest","volume","impliedVolatility"]]
                    .sort_values("openInterest", ascending=False).head(10),
                    use_container_width=True, hide_index=True,
                )
        else:
            st.warning("Could not load option chain for this expiration.")


# ==============================================================================
# TAB 4 — Short Interest & News Sentiment
# ==============================================================================
with tab4:
    st.subheader("📰 Short Interest & News Sentiment")

    col_short, col_news = st.columns([1, 2])

    # ── Short Interest ──
    with col_short:
        st.markdown("#### Short Interest Data")

        @st.cache_data(ttl=3600)
        def get_short_data(ticker):
            try:
                i = yf.Ticker(ticker).info
                return {
                    "Short % of Float":     i.get("shortPercentOfFloat"),
                    "Short Ratio (days)":   i.get("shortRatio"),
                    "Shares Short":         i.get("sharesShort"),
                    "Short % of Shares":    i.get("sharesPercentSharesOut"),
                }
            except Exception:
                return {}

        short = get_short_data(ticker)
        for k, v in short.items():
            if v is None:
                continue
            if "%" in k or "Percent" in k.lower() or "Float" in k:
                display = f"{v * 100:.2f}%"
            elif "Shares Short" == k:
                display = f"{int(v):,}"
            elif "Ratio" in k:
                display = f"{v:.1f} days"
            else:
                display = str(v)
            st.metric(k, display)

        short_pct = short.get("Short % of Float", 0) or 0
        if short_pct > 0.20:
            st.error(
                "🔴 **Very high short interest** (>20%)  \n"
                "Potential short squeeze if a bullish catalyst hits. "
                "Combined with a 200 MA reclaim, this can be explosive."
            )
        elif short_pct > 0.10:
            st.warning("⚠️ **Elevated short interest** (>10%) — watch for squeeze conditions.")
        elif short_pct > 0:
            st.success("✅ **Low short interest** — no extreme bearish crowding.")

        short_ratio = short.get("Short Ratio (days)", 0) or 0
        if short_ratio:
            with st.expander("📖 Short Ratio explained"):
                st.markdown(
                    f"A short ratio of **{short_ratio:.1f} days** means it would take "
                    f"{short_ratio:.1f} trading days for all short sellers to cover their positions "
                    f"at current average volume. Higher ratio = more explosive potential squeeze."
                )

    # ── News Sentiment ──
    with col_news:
        st.markdown("#### News Sentiment")

        # Simple keyword sentiment scorer
        POS_WORDS = {
            "beat","surge","rally","gain","growth","record","upgrade",
            "buy","bullish","profit","raises","soars","strong","exceeds",
            "outperform","expansion","optimistic","milestone","recover",
        }
        NEG_WORDS = {
            "miss","drop","fall","loss","decline","concern","warning",
            "downgrade","sell","bearish","crash","cut","slump","disappoints",
            "layoffs","recall","fraud","investigation","restructure","deficit",
        }

        def sentiment_score(text: str) -> int:
            t = text.lower()
            return sum(1 for w in POS_WORDS if w in t) - sum(1 for w in NEG_WORDS if w in t)

        def sentiment_label(score: int) -> str:
            if score > 0:  return "🟢 Positive"
            if score < 0:  return "🔴 Negative"
            return "⚪ Neutral"

        if not news_key:
            st.info(
                "🔑 Add your free **NewsAPI** key in the sidebar to enable live news sentiment.  \n"
                "Get one at [newsapi.org](https://newsapi.org) — the free plan gives 100 requests/day.",
                icon="💡",
            )
            st.caption("Preview — sample news sentiment output:")
            demo_news = pd.DataFrame([
                {"Sentiment":"🟢 Positive","Date":"2024-06-01",
                 "Headline":"Apple beats Q4 earnings expectations, raises guidance"},
                {"Sentiment":"🔴 Negative","Date":"2024-05-31",
                 "Headline":"Supply chain disruptions weigh on outlook"},
                {"Sentiment":"⚪ Neutral",  "Date":"2024-05-30",
                 "Headline":"Apple announces new product event for next month"},
                {"Sentiment":"🟢 Positive","Date":"2024-05-29",
                 "Headline":"Institutional buying accelerates ahead of earnings"},
            ])
            st.dataframe(demo_news, use_container_width=True, hide_index=True)

        else:
            @st.cache_data(ttl=1800)
            def fetch_news(api_key, query, page_size=30):
                url = "https://newsapi.org/v2/everything"
                params = {
                    "q":        query,
                    "language": "en",
                    "sortBy":   "publishedAt",
                    "pageSize": page_size,
                    "apiKey":   api_key,
                }
                try:
                    r = requests.get(url, params=params, timeout=10)
                    if r.status_code == 200:
                        return r.json().get("articles", [])
                    st.warning(f"NewsAPI status {r.status_code}: {r.text[:200]}")
                except Exception as e:
                    st.error(f"NewsAPI request failed: {e}")
                return []

            search_q = f"{ticker} {info.get('longName', '')} stock"
            with st.spinner("Fetching news…"):
                articles = fetch_news(news_key, search_q)

            if articles:
                scored = []
                for a in articles:
                    text  = (a.get("title") or "") + " " + (a.get("description") or "")
                    score = sentiment_score(text)
                    scored.append({
                        "Sentiment": sentiment_label(score),
                        "Score":     score,
                        "Date":      (a.get("publishedAt") or "")[:10],
                        "Source":    (a.get("source") or {}).get("name", "—"),
                        "Headline":  a.get("title", "—"),
                        "URL":       a.get("url", "#"),
                    })

                scores     = [s["Score"] for s in scored]
                avg_score  = np.mean(scores) if scores else 0
                n_pos      = sum(1 for s in scores if s > 0)
                n_neg      = sum(1 for s in scores if s < 0)
                n_neu      = sum(1 for s in scores if s == 0)

                s1, s2, s3, s4 = st.columns(4)
                s1.metric("Avg Sentiment",  f"{avg_score:+.1f}",
                          "Positive 🟢" if avg_score > 0 else ("Negative 🔴" if avg_score < 0 else "Neutral"))
                s2.metric("🟢 Positive",    n_pos)
                s3.metric("🔴 Negative",    n_neg)
                s4.metric("⚪ Neutral",     n_neu)

                if avg_score > 1:
                    st.success("🟢 News sentiment is **positive** — bullish media narrative.")
                elif avg_score < -1:
                    st.error("🔴 News sentiment is **negative** — bearish media narrative.")
                else:
                    st.info("⚪ News sentiment is **mixed / neutral**.")

                st.markdown("---")
                for s in scored[:15]:
                    label = s["Sentiment"]
                    date  = s["Date"]
                    src   = s["Source"]
                    head  = s["Headline"]
                    url   = s["URL"]
                    st.markdown(f"**{label}** · `{date}` · *{src}*  \n[{head}]({url})")
                    st.divider()

                if st.button("🔄 Refresh News"):
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.warning("No articles found. Try a different ticker or check your API key.")

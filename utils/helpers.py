# =============================================================================
#  utils/helpers.py
#  Shared utilities — indicators, colours, charts
#  Used by both Bitcoin and Stock apps
# =============================================================================

import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta

# ── Colour palette ─────────────────────────────────────────────────────────────
BULL_COLOR  = "#00c896"
BEAR_COLOR  = "#ff4e6a"
MA200_COLOR = "#f5a623"
MA50_COLOR  = "#4fc3f7"
MA20_COLOR  = "#ce93d8"
BG_COLOR    = "#0e1117"
GRID_COLOR  = "#1e2530"
TEXT_COLOR  = "#e0e0e0"
CARD_BG     = "#1a1f2e"


def get_plotly_layout(title: str = "", height: int = 500) -> dict:
    """Return a consistent dark-theme Plotly layout dict."""
    return dict(
        title=dict(text=title, font=dict(color=TEXT_COLOR, size=16)),
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR),
        height=height,
        xaxis=dict(gridcolor=GRID_COLOR, showgrid=True, zeroline=False),
        yaxis=dict(gridcolor=GRID_COLOR, showgrid=True, zeroline=False),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=GRID_COLOR),
        margin=dict(l=50, r=20, t=50, b=50),
        hovermode="x unified",
    )


# ── Data fetching ──────────────────────────────────────────────────────────────
def fetch_ohlcv(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Download OHLCV data from Yahoo Finance and normalise column names."""
    df = yf.download(ticker, period=period, interval=interval,
                     progress=False, auto_adjust=True)
    if df.empty:
        return df
    # Flatten MultiIndex columns yfinance sometimes returns
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df.dropna(inplace=True)
    return df


# ── Technical indicators ───────────────────────────────────────────────────────
def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add MA20, MA50, MA200, RSI, MACD, rolling volatility, regime label."""
    df = df.copy()

    close = df["Close"].squeeze()   # ensure 1-D Series

    df["MA20"]  = close.rolling(20).mean()
    df["MA50"]  = close.rolling(50).mean()
    df["MA200"] = close.rolling(200).mean()

    # RSI (14)
    df["RSI"] = ta.momentum.RSIIndicator(close, window=14).rsi()

    # MACD
    macd_obj         = ta.trend.MACD(close)
    df["MACD"]       = macd_obj.macd()
    df["MACD_signal"]= macd_obj.macd_signal()
    df["MACD_hist"]  = macd_obj.macd_diff()

    # 30-day annualised rolling volatility (%)
    df["Volatility"] = close.pct_change().rolling(30).std() * np.sqrt(252) * 100

    # Macro regime
    df["Regime"] = np.where(close >= df["MA200"], "bull", "bear")

    return df


def ma200_status(df: pd.DataFrame) -> dict:
    """Return a dict with label, colour, and % distance from 200 MA."""
    latest = df.iloc[-1]
    price  = float(latest["Close"].squeeze() if hasattr(latest["Close"], "squeeze") else latest["Close"])
    ma200  = float(latest["MA200"].squeeze() if hasattr(latest["MA200"], "squeeze") else latest["MA200"])

    if pd.isna(ma200):
        return {"label": "Insufficient data for 200 MA", "color": "#9e9e9e", "pct": 0.0}

    pct = ((price - ma200) / ma200) * 100
    if price >= ma200:
        return {
            "label": "Above 200 MA — Bull Market Structure ✅",
            "color": BULL_COLOR,
            "pct":   pct,
        }
    return {
        "label": "Below 200 MA — Zone of Interest 🔴",
        "color": BEAR_COLOR,
        "pct":   pct,
    }


# ── Shared charts ──────────────────────────────────────────────────────────────
def build_price_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Candlestick + MA ribbons + Volume + RSI — 3-row subplot."""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.60, 0.20, 0.20],
        vertical_spacing=0.03,
        subplot_titles=("Price & Moving Averages", "Volume", "RSI (14)"),
    )

    # Row 1 — candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        name="Price",
        increasing_line_color=BULL_COLOR,
        decreasing_line_color=BEAR_COLOR,
    ), row=1, col=1)

    # Moving averages
    for col_name, color, label in [
        ("MA20",  MA20_COLOR,  "20 MA"),
        ("MA50",  MA50_COLOR,  "50 MA"),
        ("MA200", MA200_COLOR, "200 MA ★"),
    ]:
        fig.add_trace(go.Scatter(
            x=df.index, y=df[col_name],
            line=dict(color=color, width=1.8 if col_name == "MA200" else 1.2),
            name=label,
        ), row=1, col=1)

    # Row 2 — volume bars
    bar_colors = [BULL_COLOR if c >= o else BEAR_COLOR
                  for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        marker_color=bar_colors,
        name="Volume",
        showlegend=False,
    ), row=2, col=1)

    # Row 3 — RSI
    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI"],
        line=dict(color="#b39ddb", width=1.5),
        name="RSI",
    ), row=3, col=1)
    for level, color in [(70, BEAR_COLOR), (30, BULL_COLOR), (50, "#555")]:
        fig.add_hline(y=level, line_dash="dot", line_color=color,
                      line_width=1, row=3, col=1)

    layout = get_plotly_layout(f"{ticker} — Price & Moving Averages", height=720)
    layout["xaxis_rangeslider_visible"] = False
    fig.update_layout(**layout)
    fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False)
    return fig


def build_volatility_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """30-day rolling annualised volatility with bull/bear regime colouring."""
    fig = go.Figure()

    # Regime-shaded fills
    for regime, fill_color in [("bull", "rgba(0,200,150,0.10)"), ("bear", "rgba(255,78,106,0.10)")]:
        mask = df["Regime"] == regime
        seg  = df[mask]
        if not seg.empty:
            fig.add_trace(go.Scatter(
                x=seg.index, y=seg["Volatility"],
                fill="tozeroy",
                fillcolor=fill_color,
                line=dict(width=0),
                showlegend=False,
            ))

    # Main volatility line
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Volatility"],
        line=dict(color=MA50_COLOR, width=1.8),
        name="30d Volatility (%)",
    ))

    fig.update_layout(**get_plotly_layout(
        f"{ticker} — 30-Day Rolling Volatility (Annualised %)", height=320))
    return fig


# ── CSS card helper ────────────────────────────────────────────────────────────
SHARED_CSS = """
<style>
body, .main { background-color: #0e1117; }
.metric-card {
    background: #1a1f2e;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 10px;
    border-left: 4px solid;
}
.stTabs [data-baseweb="tab"] {
    color: #e0e0e0;
    font-size: 14px;
}
div[data-testid="stMetricValue"] { font-size: 1.3rem; }
</style>
"""

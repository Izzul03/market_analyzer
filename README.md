# 📊 Market Analyser Suite

A full-stack market analysis app covering **Bitcoin/Crypto** and **Stocks**, built with a Benjamin Cowen–inspired macro framework centred on the **200-day Moving Average**.

Built as a data analyst portfolio project.

---

## 🚀 Quick Start

```bash
# 1. Clone / download this project
# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run Home.py
```


---

## 📁 Project Structure

```
market_analyzer/
├── Home.py                        ← Landing page (run this)
├── pages/
│   ├── 1_BTC_Analyser.py          ← Bitcoin & Crypto app
│   └── 2_Stock_Analyser.py        ← Stock market app
├── utils/
│   ├── __init__.py
│   └── helpers.py                 ← Shared indicators, charts, colours
├── requirements.txt
└── .streamlit/
    └── config.toml                ← Dark theme
```

---

## ₿ Bitcoin App — What's Inside

| Tab | Features | API |
|-----|----------|-----|
| Price & 200 MA | Candlestick, MA20/50/200, Volume, RSI, Volatility | yfinance (free) |
| Whale Activity | Large tx feed, exchange flow signals | Whale Alert (free key) |
| On-Chain Signals | Fees, mempool, hashrate trend | Mempool.space (no key) |
| Order Book / Liquidity | Depth chart + heatmap, buy/sell walls | Binance (no key) |

## 📈 Stock App — What's Inside

| Tab | Features | API |
|-----|----------|-----|
| Price & 200 MA | Candlestick, MA20/50/200, Volume, RSI, Volatility, Fundamentals | yfinance (free) |
| Insider / Institutional | SEC Form 4 insider txns, institutional holders | yfinance/SEC (no key) |
| Options Flow | P/C ratio, Max Pain, OI by strike chart | yfinance (no key) |
| Short Interest & News | Short %, short ratio, live news + sentiment scoring | yfinance + NewsAPI (free key) |

---

## 🔑 API Keys

| Key | Where | Required? |
|-----|-------|-----------|
| Whale Alert | [whale-alert.io](https://whale-alert.io) | Optional — BTC Tab 2 |
| NewsAPI | [newsapi.org](https://newsapi.org) | Optional — Stock Tab 4 |

Enter keys in the **sidebar** at runtime. No `.env` file needed.  
Binance, Mempool.space, SEC EDGAR, and yfinance all require **no key**.

---


## 📖 The 200 MA Framework

| Condition | Signal |
|-----------|--------|
| Price **above** 200 MA | Bull market structure |
| Price **below** 200 MA | Zone of interest — accumulate cautiously |
| Price **reclaims** 200 MA | Strongest confirmation signal |
| 200-**week** MA (BTC) | Ultimate long-term floor |

> *"We don't predict. We react to probabilities."* — Benjamin Cowen

---

## 🛠️ Tech Stack

Python · Streamlit · yfinance · Plotly · pandas · NumPy · ta · requests

---

*Portfolio project — not financial advice.*

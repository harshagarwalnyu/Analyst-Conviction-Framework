# Stock Market Analyst Terminal

> Institutional-grade equity intelligence — open, fast, and built for professionals who refuse to pay $24,000/year for a Bloomberg Terminal.

A full-stack financial intelligence platform that aggregates real-time market data, computes algorithmic conviction scores across the entire S&P 500 + S&P 400 universe, and delivers actionable analyst insights through a Bloomberg-inspired terminal UI. Built for portfolio managers, quant analysts, equity researchers, and sophisticated investors who demand institutional depth without the institutional price tag.

---

## Why This Exists

Every serious equity analyst knows the pain: Bloomberg costs $24K/year per seat. Refinitiv another $22K. FactSet, Capital IQ — the tab adds up before you've even made a single trade. Meanwhile the underlying data — analyst consensus, price targets, technicals, earnings estimates — is accessible. The insight gap between Wall Street and everyone else isn't the data. It's the tooling.

**This platform closes that gap.**

---

## What It Does

### Analyst Conviction Scoring Engine
The core of the platform. A proprietary scoring algorithm synthesizes multiple alpha signals into a single 0–100 conviction score per ticker:

- **Analyst consensus** — buy/hold/sell ratios weighted by recency
- **Price target upside** — distance from current price to consensus PT
- **Technical momentum** — RSI(14), SMA(50/200) golden/death cross detection
- **News sentiment** — VADER sentiment analysis across recent headlines
- **Earnings surprise history** — beat/miss patterns factored into base score

The result: an objective, data-driven ranking of every S&P 500 and S&P 400 stock, updated on demand, sortable and filterable by sector, conviction tier, or custom criteria.

### Real-Time Price Streaming
Server-Sent Events (SSE) pipeline delivers live price ticks directly to the frontend. The live marquee ticker at the top of the dashboard reflects current market prices with sub-second latency — no WebSocket overhead, no polling, no stale data.

### Full Universe Rankings
Rank the entire large-cap and mid-cap universe simultaneously. Sort by conviction score, analyst upside, sector, or momentum. Filter to Strong Buy only. Export your screened list. The kind of broad-universe view that would take hours to compile manually — available in seconds.

### Sector Intelligence
Aggregate conviction and consensus data rolled up by GICS sector. Immediately see which sectors analysts are most bullish on, which are under distribution, and where the dispersion of opinion is highest. Macro rotators and sector ETF traders get an instant edge.

### Interactive Candlestick Charts
TradingView's `lightweight-charts` library powers embedded OHLCV candlestick charts for every ticker. Fast, clean, and production-quality — the same charting engine used in professional trading platforms.

### Virtual Portfolio & Forward Testing
Build a virtual portfolio of your highest-conviction names. Track your paper P&L in real-time. Review your closed trade history. Log your top picks daily to build a verified track record of your thesis accuracy over time.

### Backtesting Engine
Test any scoring-based strategy against historical data. Simulate conviction-score-driven portfolio construction with configurable capital and lookback periods. Quantify edge before you risk real capital.

---

## Who Should Use This

| Persona | Use Case |
|---|---|
| **Equity Research Analysts** | Replace manual consensus aggregation with automated scoring across the full S&P 1500 universe |
| **Portfolio Managers** | Systematic conviction-weighted position sizing backed by real-time analyst data |
| **Quant Researchers** | Alpha signal validation — test whether analyst conviction predicts forward returns |
| **Hedge Fund Associates** | Rapid fundamental screening before deep-dive research |
| **Prop Traders** | Pre-market conviction rankings to prioritize watchlists and trade ideas |
| **Financial Advisors** | Data-backed stock selection conversations with clients |
| **Individual Investors** | Access to institutional-quality research aggregation previously gated behind $20K/year software |
| **Fintech Startups** | Production-ready financial data infrastructure that can be white-labeled or extended |

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Next.js 15 Frontend             │
│   Rankings · Ticker Detail · Portfolio · Charts  │
└───────────────────┬─────────────────────────────┘
                    │ HTTP + SSE
┌───────────────────▼─────────────────────────────┐
│               FastAPI Backend                    │
│  /rankings  /ticker  /stream  /sectors           │
│  /portfolio  /backtest  /news                    │
└───────────────────┬─────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼──────┐    ┌───────────▼──────┐
│ Conviction   │    │   yfinance API   │
│ Score Engine │    │   (market data)  │
│ RSI · SMA    │    │   analyst data   │
│ Sentiment    │    │   news · targets │
└───────┬──────┘    └──────────────────┘
        │
┌───────▼──────┐
│ SQLite DB    │
│ Portfolio    │
│ Trade Logs   │
└──────────────┘
```

**Frontend Stack**
- Next.js 15 (App Router) + React 19 + TypeScript
- Tailwind CSS 4 — Bloomberg dark terminal aesthetic
- TanStack Query v5 — intelligent server state caching
- TanStack Table v8 — virtualized high-density data grids
- `lightweight-charts` by TradingView — production candlestick charts
- Framer Motion — fluid UI transitions
- Zustand — lightweight global state
- `shadcn/ui` — accessible, unstyled component primitives
- Bun — ultra-fast JS runtime & package manager

**Backend Stack**
- FastAPI 0.135+ — async REST API with auto-generated OpenAPI schema
- Python 3.13 — latest runtime
- yfinance — market data, analyst estimates, earnings, news
- pandas + numpy — vectorized data processing pipelines
- scikit-learn — ML utilities for signal normalization
- NLTK VADER — news headline sentiment analysis
- pydantic v2 — runtime type validation & API contracts
- SSE-Starlette — Server-Sent Events for live price streaming
- uvicorn — ASGI production server
- uv — blazing fast Python package management

**Type Safety**
The frontend TypeScript types are auto-generated from the FastAPI OpenAPI schema via `openapi-typescript`. Every API call is fully typed end-to-end. No runtime surprises.

---

## Getting Started

### Prerequisites
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) — Python package manager
- [Bun](https://bun.sh) — JavaScript runtime

### Backend

```bash
cd backend
uv sync
uv run uvicorn main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
bun install
bun dev
```

Open `http://localhost:3000`

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/rankings/` | GET | Full universe rankings sorted by conviction score |
| `/api/ticker/{symbol}` | GET | Deep dive data for a single ticker |
| `/api/stream/` | GET (SSE) | Real-time price stream for live marquee |
| `/api/sectors/` | GET | Sector-level conviction aggregation |
| `/api/portfolio/` | GET / POST | Virtual portfolio holdings & trade entry |
| `/api/portfolio/{id}` | DELETE | Close a position |
| `/api/backtest/` | POST | Run historical conviction-based backtest |
| `/api/news/{symbol}` | GET | Latest news headlines for a ticker |

Full interactive documentation: `http://localhost:8000/docs`

---

## Project Structure

```
├── backend/
│   ├── main.py                 # FastAPI app entrypoint
│   ├── routes/                 # API route handlers
│   ├── schemas.py              # Pydantic request/response models
│   ├── src/
│   │   ├── api/                # Data fetching layer (yfinance)
│   │   ├── core/               # Scoring engine, backtest, models
│   │   ├── database/           # Portfolio SQLite operations
│   │   └── services/           # Analysis orchestration pipeline
│   └── tests/                  # Unit tests (conviction scoring)
│
├── frontend/
│   └── src/
│       ├── app/                # Next.js App Router pages
│       ├── components/         # Reusable UI components + shadcn
│       ├── hooks/              # usePriceStream (SSE hook)
│       └── lib/                # API client, types, utilities
│
└── README.md
```

---

## The Conviction Score — How It Works

The conviction score condenses analyst and technical signal into a normalized 0–100 value:

```
base_score = f(analyst_consensus_ratio, price_target_upside)
technical_modifier = g(RSI_14, SMA_cross_signal)
sentiment_modifier = h(VADER_compound_score, headline_volume)

conviction_score = clip(base_score + technical_modifier + sentiment_modifier, 0, 100)
```

Scores above **75** = Strong Buy tier
Scores **50–74** = Buy tier
Scores **25–49** = Hold tier
Scores below **25** = Avoid tier

The algorithm is transparent, reproducible, and auditable — unlike black-box sell-side ratings.

---

## License

MIT — use it, fork it, build on it. Financial freedom starts with open tooling.

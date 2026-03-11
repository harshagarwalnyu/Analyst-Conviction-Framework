# Stock Market Analyst Terminal

A full-stack, Bloomberg Terminal-inspired financial intelligence platform built with a modern architecture.

## Architecture

*   **Frontend**: Next.js 15 (App Router) + TypeScript + Tailwind CSS
*   **Backend**: FastAPI + Python (managed with `uv`)
*   **Real-time Data**: Server-Sent Events (SSE) for price streaming
*   **Charts**: `lightweight-charts` by TradingView
*   **Animations**: Framer Motion
*   **State Management**: Zustand & TanStack Query v5
*   **UI Components**: `shadcn/ui`

## Features

*   **Bloomberg Terminal Aesthetic**: Dark mode (`#0a0a0b`), monospace fonts, high-density data grids.
*   **Real-time Price Streaming**: SSE connection buffering high-frequency price ticks natively into React state.
*   **Algorithmic Scoring**: Backend dynamically computes `conviction_score` based on analyst consensus, technicals (RSI/SMA), and momentum.
*   **Type-Safe Contract**: Frontend strictly typed using `openapi-typescript` auto-generation from the FastAPI OpenAPI schema.

## Installation & Running

### Backend

```bash
cd backend
uv sync
uv run uvicorn main:app --port 8000
```

### Frontend

```bash
cd frontend
bun install
bun dev
```

Visit `http://localhost:3000` to interact with the dashboard.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import rankings, ticker, portfolio, backtest, stream, sector, news

app = FastAPI(
    title="Stock Market Analyst API",
    description="Backend API for the Stock Market Analyst application.",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rankings.router, prefix="/api/rankings", tags=["Rankings"])
app.include_router(ticker.router, prefix="/api/ticker", tags=["Ticker"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["Backtest"])
app.include_router(stream.router, prefix="/api/stream", tags=["Stream"])
app.include_router(sector.router, prefix="/api/sectors", tags=["Sectors"])
app.include_router(news.router, prefix="/api/news", tags=["News"])


@app.get("/")
def read_root():
    return {"message": "Welcome to Stock Market Analyst API"}

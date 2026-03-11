import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)


class PortfolioManager:
    def __init__(self, db_path="portfolio.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database tables."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Table for Trades
        c.execute("""CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticker TEXT,
                        entry_price REAL,
                        shares REAL,
                        entry_date TEXT,
                        entry_score REAL,
                        status TEXT, -- 'OPEN' or 'CLOSED'
                        exit_price REAL,
                        exit_date TEXT,
                        profit_loss REAL,
                        profit_loss_pct REAL
                    )""")

        # Table for Watchlist History (Forward Testing)
        c.execute("""CREATE TABLE IF NOT EXISTS watchlist_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        ticker TEXT,
                        rank INTEGER,
                        price REAL,
                        score REAL
                    )""")

        # Table for Market Data Cache
        c.execute("""CREATE TABLE IF NOT EXISTS market_data (
                        ticker TEXT PRIMARY KEY,
                        data_json TEXT,
                        last_updated TEXT
                    )""")

        conn.commit()
        conn.close()

    def add_trade(self, ticker, price, shares, score):
        """Record a new BUY trade."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            """INSERT INTO trades (ticker, entry_price, shares, entry_date, entry_score, status)
                     VALUES (?, ?, ?, ?, ?, 'OPEN')""",
            (ticker, price, shares, date_str, score),
        )
        conn.commit()
        conn.close()

    def close_trade(self, trade_id, exit_price):
        """Close a trade and calculate P/L."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Ensure trade_id is a native int (handle numpy.int64)
        trade_id = int(trade_id)

        # Get trade details
        c.execute("SELECT entry_price, shares FROM trades WHERE id = ?", (trade_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return None

        entry_price, shares = row
        profit_loss = (exit_price - entry_price) * shares
        profit_loss_pct = ((exit_price - entry_price) / entry_price) * 100
        exit_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute(
            """UPDATE trades 
                     SET status = 'CLOSED', exit_price = ?, exit_date = ?, profit_loss = ?, profit_loss_pct = ?
                     WHERE id = ?""",
            (exit_price, exit_date, profit_loss, profit_loss_pct, trade_id),
        )

        conn.commit()
        conn.close()
        return profit_loss

    def get_open_positions(self):
        """Get all open positions."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trades WHERE status = 'OPEN'", conn)
        conn.close()
        return df

    def get_portfolio_history(self):
        """Get all closed trades."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM trades WHERE status = 'CLOSED'", conn)
        conn.close()
        return df

    def save_daily_top_picks(self, df):
        """Save top 3 picks for the day if not already saved."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")

        # Check if we already saved for today
        c.execute("SELECT count(*) FROM watchlist_history WHERE date = ?", (today,))
        count = c.fetchone()[0]

        if count == 0:
            top_3 = df.head(3)
            for i, row in top_3.iterrows():
                c.execute(
                    """INSERT INTO watchlist_history (date, ticker, rank, price, score)
                             VALUES (?, ?, ?, ?, ?)""",
                    (
                        today,
                        row["Ticker"],
                        row["Rank"],
                        row["Current Price"],
                        row["Conviction Score"],
                    ),
                )
            conn.commit()

        conn.close()

    def get_watchlist_history(self):
        """Get watchlist history."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM watchlist_history", conn)
        conn.close()
        return df

    def reset_portfolio(self):
        """Clear all data."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM trades")
        c.execute("DELETE FROM watchlist_history")
        conn.commit()
        conn.close()

    # --- Market Data Caching ---

    def get_market_data(self, tickers):
        """Retrieve cached data for a list of tickers."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        placeholders = ",".join(["?"] * len(tickers))
        query = f"SELECT ticker, data_json FROM market_data WHERE ticker IN ({placeholders})"

        c.execute(query, tickers)
        results = c.fetchall()
        conn.close()

        data_map = {}
        for ticker, data_json in results:
            try:
                data_map[ticker] = json.loads(data_json)
            except:
                pass
        return data_map

    def save_market_data(self, data_list):
        """Save or update market data for multiple tickers."""
        if not data_list:
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for data in data_list:
            ticker = data.get("Ticker")
            if ticker:
                c.execute(
                    """INSERT OR REPLACE INTO market_data (ticker, data_json, last_updated)
                             VALUES (?, ?, ?)""",
                    (ticker, json.dumps(data, cls=NumpyEncoder), now),
                )

        conn.commit()
        conn.close()

    def get_stale_tickers(self, tickers, ttl_minutes=720):
        """Return list of tickers that are missing or older than ttl_minutes."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Check if table exists first (in case init_db wasn't run on existing db)
        try:
            c.execute("SELECT count(*) FROM market_data")
        except sqlite3.OperationalError:
            self.init_db()
            return tickers

        placeholders = ",".join(["?"] * len(tickers))
        query = f"SELECT ticker, last_updated FROM market_data WHERE ticker IN ({placeholders})"

        c.execute(query, tickers)
        results = c.fetchall()
        conn.close()

        existing_map = {row[0]: row[1] for row in results}
        stale_tickers = []

        cutoff_time = datetime.now() - timedelta(minutes=ttl_minutes)

        for ticker in tickers:
            if ticker not in existing_map:
                stale_tickers.append(ticker)
            else:
                last_updated_str = existing_map[ticker]
                try:
                    last_updated = datetime.strptime(
                        last_updated_str, "%Y-%m-%d %H:%M:%S"
                    )
                    if last_updated < cutoff_time:
                        stale_tickers.append(ticker)
                except:
                    stale_tickers.append(ticker)

        return stale_tickers

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import sqlite3
from sklearn.linear_model import LinearRegression
import numpy as np
import os
from typing import List, Dict, Any

# --- FastAPI setup ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# --- Database setup (SQLite) ---
DB_PATH = "stocks.db"
# Ensure DB file in same folder as main.py; adjust path if running from different cwd
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS stock_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    close REAL NOT NULL,
    UNIQUE(symbol, date)
)
""")
conn.commit()

# --- Company list ---
COMPANIES = {
    "AAPL": "Apple Inc.",
    "GOOGL": "Alphabet Inc.",
    "MSFT": "Microsoft Corp.",
    "TSLA": "Tesla Inc.",
    "AMZN": "Amazon.com Inc.",
    "META": "Meta Platforms Inc.",
    "NFLX": "Netflix Inc.",
    "NVDA": "NVIDIA Corp.",
    "BABA": "Alibaba Group",
    "TCS.NS": "Tata Consultancy Services"
}

# --- Helpers ---


def df_from_db_rows(rows: List[sqlite3.Row]) -> pd.DataFrame:
    """Convert DB rows (symbol, date, close) into a DataFrame with Date and Close columns."""
    if not rows:
        return pd.DataFrame(columns=["Date", "Close"])
    df = pd.DataFrame(rows, columns=["id", "symbol", "Date", "Close"])
    # Ensure Date is datetime
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[["Date", "Close"]].sort_values("Date")
    df.reset_index(drop=True, inplace=True)
    return df


def save_df_to_db(symbol: str, df: pd.DataFrame):
    """Save DataFrame (with Date, Close) into DB. Avoid duplicate dates."""
    for _, row in df.iterrows():
        # Normalize date string as YYYY-MM-DD
        date_val = row["Date"].date() if hasattr(
            row["Date"], "date") else pd.to_datetime(row["Date"]).date()
        date_str = date_val.isoformat()
        close_val = float(row["Close"])
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO stock_data (symbol, date, close) VALUES (?, ?, ?)",
                (symbol, date_str, close_val)
            )
        except Exception:
            # ignore single failures but continue
            pass
    conn.commit()


def get_rows_for_symbol(symbol: str) -> List[tuple]:
    cursor.execute(
        "SELECT id, symbol, date, close FROM stock_data WHERE symbol = ? ORDER BY date ASC", (symbol,))
    return cursor.fetchall()

# --- API endpoints ---


@app.get("/companies")
def get_companies():
    return [{"symbol": k, "name": v} for k, v in COMPANIES.items()]


@app.get("/stock/{symbol}")
def get_stock(symbol: str):
    """
    Returns:
    {
      "symbol": "AAPL",
      "high_52w": 345.12,
      "low_52w": 210.34,
      "avg_volume": 12345678,
      "predicted_price": 215.23,
      "data": [{ "date": "2025-07-01", "close": 200.15 }, ...]
    }
    """
    symbol = symbol.upper()
    try:
        # 1) Check DB for existing data
        rows = get_rows_for_symbol(symbol)
        if rows:
            # Use DB data
            df = df_from_db_rows(rows)
        else:
            # No DB data -> fetch from yfinance (1 month)
            try:
                df = yf.Ticker(symbol).history(period="1mo", interval="1d")
                if df.empty:
                    # Try fallback CSV if present
                    sample_csv = os.path.join(
                        os.path.dirname(__file__), "sample_data.csv")
                    if os.path.exists(sample_csv):
                        df = pd.read_csv(sample_csv)
                        if "Date" in df.columns:
                            df["Date"] = pd.to_datetime(df["Date"])
                    else:
                        return {"error": f"No data available for {symbol}"}
                else:
                    df.reset_index(inplace=True)
                # Save fetched data to DB
                save_df_to_db(symbol, df)
            except Exception as e:
                # final fallback: if csv present, use it
                sample_csv = os.path.join(
                    os.path.dirname(__file__), "sample_data.csv")
                if os.path.exists(sample_csv):
                    df = pd.read_csv(sample_csv)
                    if "Date" in df.columns:
                        df["Date"] = pd.to_datetime(df["Date"])
                    save_df_to_db(symbol, df)
                else:
                    return {"error": f"Failed to fetch data for {symbol}: {str(e)}"}

        # At this point, df should have Date and Close columns
        if df.empty:
            return {"error": f"No time-series data available for {symbol}"}

        # 2) 52-week stats + avg volume (we fetch 1y summary from yfinance to get volume and 52w range)
        try:
            hist_52w = yf.Ticker(symbol).history(period="1y")
            if hist_52w is not None and not hist_52w.empty:
                high_52w = float(hist_52w["Close"].max())
                low_52w = float(hist_52w["Close"].min())
                avg_volume = int(hist_52w["Volume"].mean())
            else:
                # If yf fails, set Nones / 0
                high_52w = None
                low_52w = None
                avg_volume = None
        except Exception:
            high_52w = None
            low_52w = None
            avg_volume = None

        # 3) Prediction: simple linear regression on stored df (day index -> close)
        predicted_price = None
        try:
            df_pred = df.copy().reset_index(drop=True)
            # Ensure Close numeric
            df_pred["Close"] = pd.to_numeric(df_pred["Close"], errors="coerce")
            df_pred = df_pred.dropna(subset=["Close"])
            if len(df_pred) >= 3:
                df_pred["day_num"] = np.arange(len(df_pred))
                X = df_pred[["day_num"]].values.reshape(-1, 1)
                y = df_pred["Close"].values.reshape(-1, 1)
                model = LinearRegression()
                model.fit(X, y)
                next_day = np.array([[len(df_pred)]])
                predicted_price = float(model.predict(next_day)[0][0])
                predicted_price = round(predicted_price, 2)
        except Exception:
            predicted_price = None

        # 4) Build response data list (date isoformat, close rounded)
        data_list = []
        for _, row in df.iterrows():
            # Accept either pandas Timestamp or string
            date_val = row.get("Date", None) if isinstance(
                row, dict) else row["Date"]
            if hasattr(date_val, "date"):
                date_str = date_val.date().isoformat()
            else:
                # fallback convert
                try:
                    date_str = pd.to_datetime(date_val).date().isoformat()
                except Exception:
                    date_str = str(date_val)
            close_val = float(row["Close"])
            data_list.append({"date": date_str, "close": round(close_val, 2)})

        response: Dict[str, Any] = {
            "symbol": symbol,
            "data": data_list,
            "predicted_price": predicted_price
        }
        if high_52w is not None:
            response["high_52w"] = round(high_52w, 2)
        else:
            response["high_52w"] = None
        if low_52w is not None:
            response["low_52w"] = round(low_52w, 2)
        else:
            response["low_52w"] = None
        if avg_volume is not None:
            response["avg_volume"] = int(avg_volume)
        else:
            response["avg_volume"] = None

        return response

    except Exception as e:
        return {"error": str(e)}


@app.get("/refresh/{symbol}")
def refresh_symbol(symbol: str):
    """
    Force-refresh data from yfinance for the given symbol and store/overwrite in DB.
    (It inserts new dates and ignores duplicates.)
    """
    symbol = symbol.upper()
    try:
        df = yf.Ticker(symbol).history(period="1mo", interval="1d")
        if df is None or df.empty:
            return {"error": f"No fresh data from yfinance for {symbol}"}
        df.reset_index(inplace=True)
        save_df_to_db(symbol, df)
        return {"status": "ok", "message": f"Refreshed and saved data for {symbol}"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/stored")
def get_stored(limit: int = 200):
    """
    Return up to `limit` rows from the stored DB (helpful to inspect what's saved).
    """
    cursor.execute(
        "SELECT id, symbol, date, close FROM stock_data ORDER BY symbol, date DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    out = [{"id": r[0], "symbol": r[1], "date": r[2], "close": r[3]}
           for r in rows]
    return out


@app.get("/")
def root():
    return {"message": "Stock Dashboard API running"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
from datetime import datetime

app = FastAPI()

# ========== ADD CORS MIDDLEWARE ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://givotrades.com",
    "https://www.givotrades.com"],  # later restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== FEMC ANALYZER CLASS ==========
class FEMCAnalyzer:
    def analyze(self, symbol: str, df: pd.DataFrame):
        if df.empty:
            return {"error": "No data available"}

        current_price = float(df['Close'].iloc[-1])

        ma_fast = df['Close'].rolling(window=20, min_periods=1).mean().iloc[-1]
        ma_slow = df['Close'].rolling(window=50, min_periods=1).mean().iloc[-1]

        is_bullish = ma_fast > ma_slow

        recent_high = df['High'].tail(5).max()
        recent_low = df['Low'].tail(5).min()

        if is_bullish:
            entry = recent_high * 1.0005
            stop_loss = recent_low * 0.999
            take_profit = entry + (entry - stop_loss) * 2.0
            take_profit_2 = take_profit * 1.2
            signal = "BUY"
            note = f"Bullish trend detected. MA Fast: {ma_fast:.2f} > MA Slow: {ma_slow:.2f}"
        else:
            entry = recent_low * 0.9995
            stop_loss = recent_high * 1.001
            take_profit = entry - (stop_loss - entry) * 2.0
            take_profit_2 = take_profit * 0.8
            signal = "SELL"
            note = f"Bearish trend detected. MA Fast: {ma_fast:.2f} < MA Slow: {ma_slow:.2f}"

        return {
            "symbol": symbol,
            "current_price": round(current_price, 4),
            "signal": signal,
            "entry": round(entry, 4),
            "stop_loss": round(stop_loss, 4),
            "take_profit_1": round(take_profit, 4),
            "take_profit_2": round(take_profit_2, 4),
            "trend": {
                "ma_fast": round(ma_fast, 4),
                "ma_slow": round(ma_slow, 4),
                "direction": "BULLISH" if is_bullish else "BEARISH"
            },
            "analysis_note": note,
            "timestamp": datetime.now().isoformat()
        }

analyzer = FEMCAnalyzer()

# ========== API ENDPOINTS ==========
@app.get("/")
async def home():
    return {"message": "Finanalytica API is running!", "version": "1.0"}

@app.get("/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    try:
        symbol_map = {
            "XAUUSD": "GC=F",
            "EURUSD": "EURUSD=X",
            "GBPUSD": "GBPUSD=X",
            "USDJPY": "USDJPY=X",
            "BTCUSD": "BTC-USD",
            "ETHUSD": "ETH-USD",
        }

        yahoo_symbol = symbol_map.get(symbol, symbol)

        ticker = yf.Ticker(yahoo_symbol)
        df = ticker.history(period="5d", interval="1h")

        if df.empty:
            return {"error": f"No data found for {symbol}"}

        return analyzer.analyze(symbol, df)

    except Exception as e:
        return {"error": str(e), "symbol": symbol}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

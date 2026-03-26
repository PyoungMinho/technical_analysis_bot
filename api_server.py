"""
Trading Bot API Server
Wraps us_quant_bot.py analysis into a REST API for the frontend dashboard.
"""

import warnings
warnings.filterwarnings("ignore")

import math
import numpy as np
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(title="US Quant Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def _safe_float(val, decimals=2) -> float:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return 0.0
    return round(float(val), decimals)


@app.get("/api/analyze/{ticker}")
def analyze(ticker: str):
    ticker = ticker.upper().strip()
    if not ticker.isalpha() or len(ticker) > 6:
        raise HTTPException(400, "Invalid ticker symbol")

    try:
        # ── Download price data ──
        df = yf.download(ticker, period="1y", interval="1d",
                         auto_adjust=True, progress=False)
        df = _flatten_columns(df)
        if df.empty or len(df) < 50:
            raise HTTPException(404, f"Not enough data for {ticker}")

        # ── Ticker info ──
        info = yf.Ticker(ticker).info or {}
        company_name = info.get("shortName", info.get("longName", ticker))
        high_52w = info.get("fiftyTwoWeekHigh", float(df["Close"].max()))
        low_52w = info.get("fiftyTwoWeekLow", float(df["Close"].min()))

        # ── Compute all indicators ──
        df["SMA_FAST"] = ta.trend.sma_indicator(df["Close"], window=50)
        df["SMA_SLOW"] = ta.trend.sma_indicator(df["Close"], window=200)
        df["RSI"] = ta.momentum.rsi(df["Close"], window=14)
        df["ATR"] = ta.volatility.average_true_range(df["High"], df["Low"], df["Close"], window=14)

        vol_fast = df["Volume"].rolling(5).mean()
        vol_slow = df["Volume"].rolling(20).mean()
        df["VOL_OSC"] = ((vol_fast - vol_slow) / vol_slow * 100).round(2)

        macd_ind = ta.trend.MACD(df["Close"], window_fast=12, window_slow=26, window_sign=9)
        df["MACD"] = macd_ind.macd()
        df["MACD_SIG"] = macd_ind.macd_signal()
        df["MACD_HIST"] = macd_ind.macd_diff()

        bb = ta.volatility.BollingerBands(df["Close"], window=20, window_dev=2)
        df["BB_UPPER"] = bb.bollinger_hband()
        df["BB_MIDDLE"] = bb.bollinger_mavg()
        df["BB_LOWER"] = bb.bollinger_lband()
        df["BB_PBAND"] = bb.bollinger_pband()

        stoch = ta.momentum.StochasticOscillator(df["High"], df["Low"], df["Close"], window=14, smooth_window=3)
        df["STOCH_K"] = stoch.stoch()
        df["STOCH_D"] = stoch.stoch_signal()

        adx_ind = ta.trend.ADXIndicator(df["High"], df["Low"], df["Close"], window=14)
        df["ADX"] = adx_ind.adx()

        df["MFI"] = ta.volume.money_flow_index(df["High"], df["Low"], df["Close"], df["Volume"], window=14)

        df["OBV"] = ta.volume.on_balance_volume(df["Close"], df["Volume"])
        df["OBV_SMA5"] = df["OBV"].rolling(5).mean()

        row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else row

        close = _safe_float(row["Close"])
        sma_fast = _safe_float(row["SMA_FAST"])
        sma_slow = _safe_float(row["SMA_SLOW"])
        rsi = _safe_float(row["RSI"])
        atr = _safe_float(row["ATR"])
        vol_osc = _safe_float(row["VOL_OSC"])
        macd_val = _safe_float(row["MACD"], 4)
        macd_sig = _safe_float(row["MACD_SIG"], 4)
        macd_hist = _safe_float(row["MACD_HIST"], 4)
        bb_upper = _safe_float(row["BB_UPPER"])
        bb_middle = _safe_float(row["BB_MIDDLE"])
        bb_lower = _safe_float(row["BB_LOWER"])
        bb_pband = _safe_float(row["BB_PBAND"], 4)
        stoch_k = _safe_float(row["STOCH_K"])
        stoch_d = _safe_float(row["STOCH_D"])
        adx = _safe_float(row["ADX"])
        mfi = _safe_float(row["MFI"])
        obv = _safe_float(row["OBV"], 0)
        obv_sma = _safe_float(row["OBV_SMA5"], 0)

        prev_close = _safe_float(prev_row["Close"])
        price_change = round(close - prev_close, 2)
        price_change_pct = round((price_change / prev_close) * 100, 2) if prev_close else 0

        # ── Buy/Sell conditions ──
        golden_cross = sma_fast > sma_slow
        rsi_ok = rsi < 70
        volume_ok = vol_osc > 0
        macd_bullish = macd_val > macd_sig
        bb_not_upper = bb_pband < 0.95
        stoch_not_over = stoch_k < 80
        adx_trending = adx > 25
        mfi_ok = mfi < 80
        obv_rising = obv > obv_sma

        core_buy = golden_cross and rsi_ok and volume_ok
        ext_confirms = sum([macd_bullish, bb_not_upper, stoch_not_over])
        adv_confirms = sum([adx_trending, mfi_ok, obv_rising])
        chart_buy = core_buy and ext_confirms >= 2 and adv_confirms >= 2

        death_cross = sma_fast < sma_slow
        rsi_overbought = rsi > 70
        macd_bearish = macd_val < macd_sig
        bb_at_upper = bb_pband > 0.95
        stoch_overbought = stoch_k > 80
        core_sell = death_cross and rsi_overbought
        sell_confirms = sum([macd_bearish, bb_at_upper, stoch_overbought])
        chart_sell = core_sell and sell_confirms >= 2

        # ── Trend score ──
        buy_signals = sum([golden_cross, rsi_ok, volume_ok, macd_bullish,
                          bb_not_upper, stoch_not_over, adx_trending, mfi_ok, obv_rising])
        trend_score = int(buy_signals / 9 * 100)

        # ── Signal ──
        if chart_buy:
            signal = "BUY"
        elif chart_sell:
            signal = "SELL"
        else:
            signal = "HOLD"

        # ── Risk management ──
        stop_loss = round(close - 2.0 * atr, 2)
        take_profit = round(close + 4.0 * atr, 2)
        risk = close - stop_loss
        reward = take_profit - close
        risk_reward = round(reward / risk, 2) if risk > 0 else 0

        # ── Kelly ──
        est_win_rate = max(0.3, min(0.8, trend_score / 100))
        rr = 4.0 / 2.0
        b = rr
        kelly = (b * est_win_rate - (1 - est_win_rate)) / b
        kelly_pct = round(max(0.0, min(0.25, kelly * 0.5)) * 100, 1)

        # ── Fibonacci ──
        fib_diff = high_52w - low_52w
        fib = {
            "high": round(high_52w, 2),
            "low": round(low_52w, 2),
            "level_236": round(high_52w - fib_diff * 0.236, 2),
            "level_382": round(high_52w - fib_diff * 0.382, 2),
            "level_500": round(high_52w - fib_diff * 0.500, 2),
            "level_618": round(high_52w - fib_diff * 0.618, 2),
            "level_786": round(high_52w - fib_diff * 0.786, 2),
        }

        # ── Volume formatting ──
        vol_fast_val = _safe_float(vol_fast.iloc[-1], 0)
        vol_slow_val = _safe_float(vol_slow.iloc[-1], 0)

        # ── Price history for chart (last 60 days) ──
        chart_data = []
        chart_slice = df.tail(60)
        for idx, r in chart_slice.iterrows():
            chart_data.append({
                "date": str(idx.date()),
                "close": _safe_float(r["Close"]),
                "sma50": _safe_float(r["SMA_FAST"]),
                "sma200": _safe_float(r["SMA_SLOW"]),
            })

        # ── Market Regime (VIX + SPY) ──
        regime_data = _get_market_regime()

        # ── Relative Strength ──
        rs_data = _get_relative_strength(ticker, df)

        # ── News (basic, no LLM sentiment) ──
        news_data = _get_news(ticker)

        return {
            "ticker": ticker,
            "companyName": company_name,
            "close": close,
            "priceChange": price_change,
            "priceChangePct": price_change_pct,
            "high52w": round(high_52w, 2),
            "low52w": round(low_52w, 2),
            "signal": signal,
            "trendScore": trend_score,
            "indicators": {
                "sma50": sma_fast,
                "sma200": sma_slow,
                "rsi": rsi,
                "atr": atr,
                "volOsc": vol_osc,
                "volFast": vol_fast_val,
                "volSlow": vol_slow_val,
                "macd": macd_val,
                "macdSignal": macd_sig,
                "macdHist": macd_hist,
                "bbUpper": bb_upper,
                "bbMiddle": bb_middle,
                "bbLower": bb_lower,
                "bbPband": bb_pband,
                "stochK": stoch_k,
                "stochD": stoch_d,
                "adx": adx,
                "mfi": mfi,
                "obv": obv,
                "obvSma": obv_sma,
            },
            "conditions": {
                "goldenCross": golden_cross,
                "rsiOk": rsi_ok,
                "volumeOk": volume_ok,
                "macdBullish": macd_bullish,
                "bbNotUpper": bb_not_upper,
                "stochNotOver": stoch_not_over,
                "adxTrending": adx_trending,
                "mfiOk": mfi_ok,
                "obvRising": obv_rising,
                "deathCross": death_cross,
                "rsiOverbought": rsi_overbought,
                "macdBearish": macd_bearish,
                "bbAtUpper": bb_at_upper,
                "stochOverbought": stoch_overbought,
            },
            "risk": {
                "stopLoss": stop_loss,
                "takeProfit": take_profit,
                "riskReward": risk_reward,
                "kellyPct": kelly_pct,
            },
            "fibonacci": fib,
            "chartData": chart_data,
            "regime": regime_data,
            "relativeStrength": rs_data,
            "news": news_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")


def _get_market_regime() -> dict:
    try:
        vix_df = yf.download("^VIX", period="3mo", interval="1d",
                             auto_adjust=True, progress=False)
        vix_df = _flatten_columns(vix_df)
        vix_current = _safe_float(vix_df["Close"].iloc[-1])

        if vix_current > 35:
            regime, emoji = "EXTREME_FEAR", "extreme-fear"
        elif vix_current > 25:
            regime, emoji = "HIGH_VOL", "high-vol"
        elif vix_current > 15:
            regime, emoji = "NORMAL", "normal"
        else:
            regime, emoji = "LOW_VOL", "low-vol"

        spy_df = yf.download("SPY", period="6mo", interval="1d",
                             auto_adjust=True, progress=False)
        spy_df = _flatten_columns(spy_df)
        spy_close = spy_df["Close"]
        spy_sma50 = _safe_float(spy_close.rolling(50).mean().iloc[-1])
        spy_sma200_val = spy_close.rolling(200).mean().iloc[-1] if len(spy_close) >= 200 else spy_sma50
        spy_sma200 = _safe_float(spy_sma200_val)

        if spy_sma50 > spy_sma200:
            spy_trend = "BULL"
        elif spy_sma50 < spy_sma200:
            spy_trend = "BEAR"
        else:
            spy_trend = "SIDEWAYS"

        return {
            "vix": vix_current,
            "regime": regime,
            "regimeClass": emoji,
            "spyTrend": spy_trend,
            "spySma50": spy_sma50,
            "spySma200": spy_sma200,
        }
    except Exception:
        return {"vix": 0, "regime": "UNKNOWN", "regimeClass": "normal",
                "spyTrend": "UNKNOWN", "spySma50": 0, "spySma200": 0}


def _get_relative_strength(ticker: str, df: pd.DataFrame) -> dict:
    try:
        spy_df = yf.download("SPY", period="6mo", interval="1d",
                             auto_adjust=True, progress=False)
        spy_df = _flatten_columns(spy_df)

        t_now = float(df["Close"].iloc[-1])
        t_1m = float(df["Close"].iloc[-22]) if len(df) >= 22 else t_now
        t_3m = float(df["Close"].iloc[-66]) if len(df) >= 66 else t_now
        s_now = float(spy_df["Close"].iloc[-1])
        s_1m = float(spy_df["Close"].iloc[-22]) if len(spy_df) >= 22 else s_now
        s_3m = float(spy_df["Close"].iloc[-66]) if len(spy_df) >= 66 else s_now

        t_ret_1m = round((t_now / t_1m - 1) * 100, 2)
        t_ret_3m = round((t_now / t_3m - 1) * 100, 2)
        s_ret_1m = round((s_now / s_1m - 1) * 100, 2)
        s_ret_3m = round((s_now / s_3m - 1) * 100, 2)

        return {
            "tickerReturn1m": t_ret_1m,
            "tickerReturn3m": t_ret_3m,
            "spyReturn1m": s_ret_1m,
            "spyReturn3m": s_ret_3m,
            "outperforming": t_ret_1m > s_ret_1m,
        }
    except Exception:
        return {"tickerReturn1m": 0, "tickerReturn3m": 0,
                "spyReturn1m": 0, "spyReturn3m": 0, "outperforming": False}


def _get_news(ticker: str) -> list:
    try:
        stock = yf.Ticker(ticker)
        items = []
        for raw in (stock.news or [])[:5]:
            content = raw.get("content", {})
            title = content.get("title", raw.get("title", "N/A"))
            source = (content.get("provider", {}) or {}).get(
                "displayName", raw.get("publisher", "Unknown"))
            pub_date = content.get("pubDate", raw.get("providerPublishTime", ""))
            if isinstance(pub_date, (int, float)):
                pub_date = datetime.fromtimestamp(pub_date).strftime("%Y-%m-%d %H:%M")
            elif isinstance(pub_date, str) and pub_date:
                try:
                    pub_date = datetime.fromisoformat(
                        pub_date.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    pass
            items.append({"title": title, "source": source, "published": pub_date})
        return items
    except Exception:
        return []


# Serve frontend
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/{filename}")
def serve_static(filename: str):
    filepath = os.path.join(FRONTEND_DIR, filename)
    if os.path.isfile(filepath):
        return FileResponse(filepath)
    raise HTTPException(404)


if __name__ == "__main__":
    import uvicorn
    print("\n⚡ US Quant Bot Dashboard")
    print("   http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)

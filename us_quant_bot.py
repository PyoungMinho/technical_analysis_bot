"""
US Quant Trading Bot  (Senior Quant Edition v3)
════════════════════════════════════════════════════════════════════════════
Strategy  : 10-Factor Multi-Signal
            (SMA × RSI × MACD × Bollinger × Stochastic × Volume Osc
             × ADX × MFI × OBV × Relative Strength vs SPY)
            + Multi-Timeframe Alignment (Daily + Weekly)
            + AI News Sentiment (Time-Decay Weighted)
            + VIX Market Regime Detection
            + Fibonacci Retracement Levels
            + Kelly Criterion Position Sizing
            + Earnings Calendar Warning
            + Senior Quant LLM Comprehensive Analysis
Risk Mgmt : ATR-based dynamic Stop-Loss & Take-Profit + Kelly sizing
Modes     : Interactive (custom ticker) / Single-run
════════════════════════════════════════════════════════════════════════════
"""

import warnings
warnings.filterwarnings("ignore")

import math
import os
import re
import requests
import numpy as np
import yfinance as yf
import pandas as pd
import ta
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Optional
from functools import lru_cache

load_dotenv()
_ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


# ════════════════════════════════════════════════════════════════════════════
# TICKER INFO CACHE  — avoid redundant yfinance API calls
# ════════════════════════════════════════════════════════════════════════════

class TickerCache:
    """Per-session cache for yfinance Ticker.info to avoid repeated API hits."""
    _cache: dict = {}

    @classmethod
    def get_info(cls, ticker: str) -> dict:
        if ticker not in cls._cache:
            cls._cache[ticker] = yf.Ticker(ticker).info or {}
        return cls._cache[ticker]

    @classmethod
    def clear(cls):
        cls._cache.clear()


# ════════════════════════════════════════════════════════════════════════════
# LLM PROVIDERS
# ════════════════════════════════════════════════════════════════════════════

class BaseLLMProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str: ...

    def complete_long(self, prompt: str) -> str:
        return self.complete(prompt)

    @property
    @abstractmethod
    def label(self) -> str: ...


class OllamaProvider(BaseLLMProvider):
    def __init__(self, model: str = "llama3", host: str = "http://localhost:11434"):
        self.model = model
        self.host  = host

    @property
    def label(self) -> str:
        return f"Ollama / {self.model}  (local)"

    def complete(self, prompt: str) -> str:
        return self._call(prompt)

    def complete_long(self, prompt: str) -> str:
        return self._call(prompt)

    def _call(self, prompt: str) -> str:
        try:
            resp = requests.post(
                f"{self.host}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=120,
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Ollama 서버에 연결할 수 없습니다.\n"
                "  터미널에서 'ollama serve' 를 먼저 실행하세요."
            )
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"Ollama 오류 ({e.response.status_code}). "
                f"모델이 없다면: ollama pull {self.model}"
            )


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str = ""):
        import anthropic as _anthropic
        self.model = model
        key = api_key or _ANTHROPIC_API_KEY
        if not key.startswith("sk-ant-"):
            raise ValueError(
                "\n  ❌  ANTHROPIC_API_KEY 가 설정되지 않았습니다.\n"
                "  .env 파일에서 키를 입력한 뒤 다시 실행하세요.\n"
                "  ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxx"
            )
        self._client = _anthropic.Anthropic(api_key=key)

    @property
    def label(self) -> str:
        return f"Anthropic / {self.model}"

    def complete(self, prompt: str) -> str:
        response = self._client.messages.create(
            model=self.model, max_tokens=16,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    def complete_long(self, prompt: str) -> str:
        response = self._client.messages.create(
            model=self.model, max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()


# ════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class FibonacciLevels:
    """52주 고/저 기반 피보나치 되돌림 레벨."""
    high_52w       : float
    low_52w        : float
    level_236      : float   # 23.6%
    level_382      : float   # 38.2%
    level_500      : float   # 50.0%
    level_618      : float   # 61.8%
    level_786      : float   # 78.6%
    nearest_support: str = ""   # 현재가 기준 가장 가까운 지지선
    nearest_resist : str = ""   # 현재가 기준 가장 가까운 저항선


@dataclass
class MarketRegime:
    """VIX 기반 시장 레짐 분석."""
    vix_current    : float
    vix_sma20      : float
    regime         : str     # "LOW_VOL" | "NORMAL" | "HIGH_VOL" | "EXTREME_FEAR"
    regime_label   : str     # 한글 설명
    spy_trend      : str     # SPY 추세 ("BULL" | "BEAR" | "SIDEWAYS")
    spy_rsi        : float
    spy_change_1m  : float   # SPY 1개월 수익률


@dataclass
class RelativeStrength:
    """종목 vs SPY 상대강도."""
    ticker_return_1m : float
    ticker_return_3m : float
    spy_return_1m    : float
    spy_return_3m    : float
    rs_ratio_1m      : float   # ticker / spy (>1 = outperform)
    rs_ratio_3m      : float
    outperforming    : bool    # 1개월 기준 SPY 대비 아웃퍼폼 여부


@dataclass
class Signal:
    date           : str
    ticker         : str
    close          : float
    # ── Core indicators ──
    sma_fast       : float
    sma_slow       : float
    rsi            : float
    atr            : float
    vol_oscillator : float
    # ── Extended indicators ──
    macd           : float = 0.0
    macd_signal    : float = 0.0
    macd_histogram : float = 0.0
    bb_upper       : float = 0.0
    bb_middle      : float = 0.0
    bb_lower       : float = 0.0
    bb_pband       : float = 0.0
    stoch_k        : float = 0.0
    stoch_d        : float = 0.0
    # ── NEW: Advanced indicators ──
    adx            : float = 0.0     # Average Directional Index (추세 강도)
    mfi            : float = 0.0     # Money Flow Index (자금 흐름)
    obv_slope      : float = 0.0     # OBV 기울기 (자금 유입/유출 방향)
    # ── Buy condition flags ──
    golden_cross   : bool = False
    rsi_ok         : bool = False
    volume_ok      : bool = False
    macd_bullish   : bool = False
    bb_not_upper   : bool = False
    stoch_not_over : bool = False
    adx_trending   : bool = False    # ADX > 25 (추세 존재)
    mfi_ok         : bool = False    # MFI < 80 (과매수 아님)
    obv_rising     : bool = False    # OBV 상승중
    # ── Composite flags ──
    chart_buy      : bool = False
    chart_sell     : bool = False
    # ── Sell condition flags ──
    death_cross    : bool = False
    rsi_oversold   : bool = False
    macd_bearish   : bool = False
    bb_at_upper    : bool = False
    stoch_overbought: bool = False
    # ── Multi-timeframe ──
    weekly_trend_aligned : bool = False   # 주봉 추세와 일봉 일치 여부
    weekly_sma_cross     : str  = ""      # "GOLDEN" | "DEATH" | "NEUTRAL"
    # ── Risk levels ──
    stop_loss      : Optional[float] = None
    take_profit    : Optional[float] = None
    risk_reward    : Optional[float] = None
    # ── Trend strength score (0-100) ──
    trend_score    : int = 0
    # ── Kelly criterion ──
    kelly_fraction : float = 0.0     # 추천 포지션 비율
    # ── Fibonacci ──
    fibonacci      : Optional[FibonacciLevels] = None
    # ── Earnings ──
    earnings_date  : str = ""
    earnings_warning: str = ""


@dataclass
class NewsItem:
    title          : str
    summary        : str
    link           : str
    source         : str = ""
    published      : str = ""
    sentiment_score: float = 0.0
    weight         : float = 1.0


@dataclass
class TradingDecision:
    signal             : Signal
    news_items         : list[NewsItem]
    weighted_sentiment : float
    final_action       : str
    quant_analysis     : str = ""
    sector_info        : str = ""
    market_regime      : Optional[MarketRegime] = None
    relative_strength  : Optional[RelativeStrength] = None


# ════════════════════════════════════════════════════════════════════════════
# MARKET REGIME DETECTOR
# ════════════════════════════════════════════════════════════════════════════

class MarketRegimeDetector:
    """VIX + SPY 기반 시장 환경 분석."""

    @staticmethod
    def detect() -> MarketRegime:
        # VIX
        vix_df = yf.download("^VIX", period="3mo", interval="1d",
                             auto_adjust=True, progress=False)
        if isinstance(vix_df.columns, pd.MultiIndex):
            vix_df.columns = vix_df.columns.get_level_values(0)
        vix_current = float(vix_df["Close"].iloc[-1])
        vix_sma20   = float(vix_df["Close"].rolling(20).mean().iloc[-1])

        if vix_current > 35:
            regime, label = "EXTREME_FEAR", "🔴 극단적 공포 (VIX>35)"
        elif vix_current > 25:
            regime, label = "HIGH_VOL", "🟠 높은 변동성 (VIX 25-35)"
        elif vix_current > 15:
            regime, label = "NORMAL", "🟢 정상 (VIX 15-25)"
        else:
            regime, label = "LOW_VOL", "🔵 낮은 변동성 (VIX<15)"

        # SPY
        spy_df = yf.download("SPY", period="6mo", interval="1d",
                             auto_adjust=True, progress=False)
        if isinstance(spy_df.columns, pd.MultiIndex):
            spy_df.columns = spy_df.columns.get_level_values(0)

        spy_close    = spy_df["Close"]
        spy_sma50    = spy_close.rolling(50).mean().iloc[-1]
        spy_sma200   = spy_close.rolling(200).mean().iloc[-1] if len(spy_close) >= 200 else spy_sma50
        spy_rsi      = float(ta.momentum.rsi(spy_close, window=14).iloc[-1])
        spy_now      = float(spy_close.iloc[-1])
        spy_1m_ago   = float(spy_close.iloc[-22]) if len(spy_close) >= 22 else spy_now
        spy_change   = round((spy_now / spy_1m_ago - 1) * 100, 2)

        if spy_sma50 > spy_sma200:
            spy_trend = "BULL"
        elif spy_sma50 < spy_sma200:
            spy_trend = "BEAR"
        else:
            spy_trend = "SIDEWAYS"

        return MarketRegime(
            vix_current=round(vix_current, 2),
            vix_sma20=round(vix_sma20, 2),
            regime=regime, regime_label=label,
            spy_trend=spy_trend,
            spy_rsi=round(spy_rsi, 2),
            spy_change_1m=spy_change,
        )


# ════════════════════════════════════════════════════════════════════════════
# SIGNAL GENERATOR  (10-Factor + Multi-Timeframe)
# ════════════════════════════════════════════════════════════════════════════

class SignalGenerator:
    def __init__(
        self,
        sma_fast       : int   = 50,
        sma_slow       : int   = 200,
        rsi_period     : int   = 14,
        rsi_overbought : float = 70.0,
        rsi_oversold   : float = 30.0,
        atr_period     : int   = 14,
        atr_stop_mult  : float = 2.0,
        atr_target_mult: float = 4.0,
        vol_fast       : int   = 5,
        vol_slow       : int   = 20,
        macd_fast      : int   = 12,
        macd_slow      : int   = 26,
        macd_signal    : int   = 9,
        bb_period      : int   = 20,
        bb_std         : float = 2.0,
        stoch_period   : int   = 14,
        stoch_smooth   : int   = 3,
        adx_period     : int   = 14,
        mfi_period     : int   = 14,
    ):
        self.sma_fast        = sma_fast
        self.sma_slow        = sma_slow
        self.rsi_period      = rsi_period
        self.rsi_overbought  = rsi_overbought
        self.rsi_oversold    = rsi_oversold
        self.atr_period      = atr_period
        self.atr_stop_mult   = atr_stop_mult
        self.atr_target_mult = atr_target_mult
        self.vol_fast        = vol_fast
        self.vol_slow        = vol_slow
        self.macd_fast       = macd_fast
        self.macd_slow       = macd_slow
        self.macd_signal_p   = macd_signal
        self.bb_period       = bb_period
        self.bb_std          = bb_std
        self.stoch_period    = stoch_period
        self.stoch_smooth    = stoch_smooth
        self.adx_period      = adx_period
        self.mfi_period      = mfi_period

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # ── Core ──
        df["SMA_FAST"] = ta.trend.sma_indicator(df["Close"], window=self.sma_fast)
        df["SMA_SLOW"] = ta.trend.sma_indicator(df["Close"], window=self.sma_slow)
        df["RSI"]      = ta.momentum.rsi(df["Close"], window=self.rsi_period)
        df["ATR"]      = ta.volatility.average_true_range(
            df["High"], df["Low"], df["Close"], window=self.atr_period
        )
        vol_fast_ma   = df["Volume"].rolling(self.vol_fast).mean()
        vol_slow_ma   = df["Volume"].rolling(self.vol_slow).mean()
        df["VOL_OSC"] = ((vol_fast_ma - vol_slow_ma) / vol_slow_ma * 100).round(2)

        # ── MACD ──
        macd_ind = ta.trend.MACD(
            df["Close"], window_fast=self.macd_fast,
            window_slow=self.macd_slow, window_sign=self.macd_signal_p,
        )
        df["MACD"]      = macd_ind.macd()
        df["MACD_SIG"]  = macd_ind.macd_signal()
        df["MACD_HIST"] = macd_ind.macd_diff()

        # ── Bollinger Bands ──
        bb = ta.volatility.BollingerBands(
            df["Close"], window=self.bb_period, window_dev=self.bb_std
        )
        df["BB_UPPER"]  = bb.bollinger_hband()
        df["BB_MIDDLE"] = bb.bollinger_mavg()
        df["BB_LOWER"]  = bb.bollinger_lband()
        df["BB_PBAND"]  = bb.bollinger_pband()

        # ── Stochastic ──
        stoch = ta.momentum.StochasticOscillator(
            df["High"], df["Low"], df["Close"],
            window=self.stoch_period, smooth_window=self.stoch_smooth,
        )
        df["STOCH_K"] = stoch.stoch()
        df["STOCH_D"] = stoch.stoch_signal()

        # ── ADX (Average Directional Index) ──
        adx_ind = ta.trend.ADXIndicator(
            df["High"], df["Low"], df["Close"], window=self.adx_period
        )
        df["ADX"] = adx_ind.adx()

        # ── MFI (Money Flow Index) ──
        df["MFI"] = ta.volume.money_flow_index(
            df["High"], df["Low"], df["Close"], df["Volume"],
            window=self.mfi_period,
        )

        # ── OBV (On-Balance Volume) ──
        df["OBV"] = ta.volume.on_balance_volume(df["Close"], df["Volume"])
        df["OBV_SMA5"] = df["OBV"].rolling(5).mean()

        return df

    def _compute_fibonacci(self, ticker: str, close: float) -> FibonacciLevels:
        info = TickerCache.get_info(ticker)
        high = info.get("fiftyTwoWeekHigh", close * 1.1)
        low  = info.get("fiftyTwoWeekLow",  close * 0.9)
        diff = high - low

        levels = {
            "23.6%": round(high - diff * 0.236, 2),
            "38.2%": round(high - diff * 0.382, 2),
            "50.0%": round(high - diff * 0.500, 2),
            "61.8%": round(high - diff * 0.618, 2),
            "78.6%": round(high - diff * 0.786, 2),
        }

        # Find nearest support (below close) and resistance (above close)
        all_levels = [(k, v) for k, v in levels.items()]
        supports = [(k, v) for k, v in all_levels if v < close]
        resists  = [(k, v) for k, v in all_levels if v >= close]

        nearest_sup = supports[-1] if supports else ("52w Low", low)
        nearest_res = resists[0]   if resists  else ("52w High", high)

        return FibonacciLevels(
            high_52w=round(high, 2), low_52w=round(low, 2),
            level_236=levels["23.6%"], level_382=levels["38.2%"],
            level_500=levels["50.0%"], level_618=levels["61.8%"],
            level_786=levels["78.6%"],
            nearest_support=f"{nearest_sup[0]} (${nearest_sup[1]})",
            nearest_resist=f"{nearest_res[0]} (${nearest_res[1]})",
        )

    def _get_weekly_trend(self, ticker: str) -> tuple[bool, str]:
        """주봉 데이터로 트렌드 정렬 여부 확인."""
        try:
            wdf = yf.download(ticker, period="2y", interval="1wk",
                              auto_adjust=True, progress=False)
            if isinstance(wdf.columns, pd.MultiIndex):
                wdf.columns = wdf.columns.get_level_values(0)
            if len(wdf) < 50:
                return True, "NEUTRAL"
            w_sma50 = wdf["Close"].rolling(50).mean().iloc[-1]
            w_sma20 = wdf["Close"].rolling(20).mean().iloc[-1]
            if w_sma20 > w_sma50:
                return True, "GOLDEN"
            elif w_sma20 < w_sma50:
                return False, "DEATH"
            return True, "NEUTRAL"
        except Exception:
            return True, "NEUTRAL"

    def _get_earnings_warning(self, ticker: str) -> tuple[str, str]:
        """다가오는 실적발표일 확인 및 경고."""
        try:
            stock = yf.Ticker(ticker)
            cal = stock.calendar
            if cal is None or (isinstance(cal, pd.DataFrame) and cal.empty):
                return "", ""
            # calendar can be dict or DataFrame
            if isinstance(cal, dict):
                earnings = cal.get("Earnings Date", [])
                if isinstance(earnings, list) and len(earnings) > 0:
                    e_date = earnings[0]
                else:
                    return "", ""
            else:
                return "", ""

            if hasattr(e_date, 'date'):
                e_str = str(e_date.date())
                days_until = (e_date.date() - datetime.now().date()).days if hasattr(e_date, 'date') else 999
            elif isinstance(e_date, str):
                e_str = e_date
                try:
                    days_until = (datetime.strptime(e_date, "%Y-%m-%d").date() - datetime.now().date()).days
                except ValueError:
                    days_until = 999
            else:
                e_str = str(e_date)
                days_until = 999

            if 0 <= days_until <= 7:
                return e_str, f"⚠️  실적발표 {days_until}일 후! 진입 주의 (변동성 급증 예상)"
            elif 0 <= days_until <= 14:
                return e_str, f"📅  실적발표 {days_until}일 후 — 포지션 사이즈 축소 권장"
            elif days_until < 0 and days_until >= -3:
                return e_str, "📊  실적발표 직후 — 실적 반응 확인 후 진입 권장"
            return e_str, ""
        except Exception:
            return "", ""

    def _compute_relative_strength(self, ticker: str, df: pd.DataFrame) -> RelativeStrength:
        """종목 vs SPY 상대강도 계산."""
        try:
            spy_df = yf.download("SPY", period="6mo", interval="1d",
                                 auto_adjust=True, progress=False)
            if isinstance(spy_df.columns, pd.MultiIndex):
                spy_df.columns = spy_df.columns.get_level_values(0)

            t_now  = float(df["Close"].iloc[-1])
            t_1m   = float(df["Close"].iloc[-22]) if len(df) >= 22 else t_now
            t_3m   = float(df["Close"].iloc[-66]) if len(df) >= 66 else t_now
            s_now  = float(spy_df["Close"].iloc[-1])
            s_1m   = float(spy_df["Close"].iloc[-22]) if len(spy_df) >= 22 else s_now
            s_3m   = float(spy_df["Close"].iloc[-66]) if len(spy_df) >= 66 else s_now

            t_ret_1m = round((t_now / t_1m - 1) * 100, 2)
            t_ret_3m = round((t_now / t_3m - 1) * 100, 2)
            s_ret_1m = round((s_now / s_1m - 1) * 100, 2)
            s_ret_3m = round((s_now / s_3m - 1) * 100, 2)

            rs_1m = round(t_ret_1m - s_ret_1m, 2) if s_ret_1m != 0 else 0
            rs_3m = round(t_ret_3m - s_ret_3m, 2) if s_ret_3m != 0 else 0

            return RelativeStrength(
                ticker_return_1m=t_ret_1m, ticker_return_3m=t_ret_3m,
                spy_return_1m=s_ret_1m, spy_return_3m=s_ret_3m,
                rs_ratio_1m=rs_1m, rs_ratio_3m=rs_3m,
                outperforming=t_ret_1m > s_ret_1m,
            )
        except Exception:
            return RelativeStrength(0, 0, 0, 0, 0, 0, False)

    def _kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Kelly Criterion: f* = (bp - q) / b  where b = avg_win/avg_loss."""
        if avg_loss == 0:
            return 0.0
        b = abs(avg_win / avg_loss)
        p = win_rate
        q = 1 - p
        kelly = (b * p - q) / b
        # Half-Kelly (보수적), 0-25% 범위로 클램프
        return round(max(0.0, min(0.25, kelly * 0.5)) * 100, 1)

    def generate(self, ticker: str, df: pd.DataFrame) -> Signal:
        df_ind = self.compute_indicators(df)
        row = df_ind.iloc[-1]

        close     = float(row["Close"])
        sma_fast  = float(row["SMA_FAST"])
        sma_slow  = float(row["SMA_SLOW"])
        rsi       = float(row["RSI"])
        atr       = float(row["ATR"])
        vol_osc   = float(row["VOL_OSC"])
        macd_val  = float(row["MACD"])
        macd_sig  = float(row["MACD_SIG"])
        macd_hist = float(row["MACD_HIST"])
        bb_upper  = float(row["BB_UPPER"])
        bb_middle = float(row["BB_MIDDLE"])
        bb_lower  = float(row["BB_LOWER"])
        bb_pband  = float(row["BB_PBAND"])
        stoch_k   = float(row["STOCH_K"])
        stoch_d   = float(row["STOCH_D"])
        adx       = float(row["ADX"])
        mfi       = float(row["MFI"])
        obv_now   = float(row["OBV"])
        obv_sma   = float(row["OBV_SMA5"])

        # ── BUY conditions (10-factor) ──
        golden_cross   = sma_fast > sma_slow
        rsi_ok         = rsi < self.rsi_overbought
        volume_ok      = vol_osc > 0
        macd_bullish   = macd_val > macd_sig
        bb_not_upper   = bb_pband < 0.95
        stoch_not_over = stoch_k < 80
        adx_trending   = adx > 25           # 추세 존재
        mfi_ok         = mfi < 80            # 과매수 아님
        obv_rising     = obv_now > obv_sma   # 자금 유입

        # Core buy (3) + Extended (3) + Advanced (3) = 9 factors
        core_buy     = golden_cross and rsi_ok and volume_ok
        ext_confirms = sum([macd_bullish, bb_not_upper, stoch_not_over])
        adv_confirms = sum([adx_trending, mfi_ok, obv_rising])
        chart_buy    = core_buy and ext_confirms >= 2 and adv_confirms >= 2

        # ── SELL conditions ──
        death_cross      = sma_fast < sma_slow
        rsi_overbought_f = rsi > self.rsi_overbought
        macd_bearish     = macd_val < macd_sig
        bb_at_upper      = bb_pband > 0.95
        stoch_overbought = stoch_k > 80

        core_sell     = death_cross and rsi_overbought_f
        sell_confirms = sum([macd_bearish, bb_at_upper, stoch_overbought])
        chart_sell    = core_sell and sell_confirms >= 2

        # ── Multi-timeframe alignment ──
        weekly_aligned, weekly_cross = self._get_weekly_trend(ticker)

        # Daily buy + weekly bearish = downgrade
        if chart_buy and not weekly_aligned:
            chart_buy = False  # 주봉 확인 못 하면 매수 취소

        # ── Trend strength (0-100), 9 factors ──
        buy_signals = sum([
            golden_cross, rsi_ok, volume_ok,
            macd_bullish, bb_not_upper, stoch_not_over,
            adx_trending, mfi_ok, obv_rising,
        ])
        trend_score = int(buy_signals / 9 * 100)

        # ── Fibonacci ──
        fibonacci = self._compute_fibonacci(ticker, close)

        # ── Earnings warning ──
        earnings_date, earnings_warning = self._get_earnings_warning(ticker)

        # ── Kelly Criterion (simple estimate from trend score) ──
        est_win_rate = trend_score / 100
        est_win_rate = max(0.3, min(0.8, est_win_rate))
        rr = self.atr_target_mult / self.atr_stop_mult
        kelly_f = self._kelly_criterion(est_win_rate, rr, 1.0)

        # ── ATR-based risk levels ──
        stop_loss = take_profit = risk_reward = None
        if chart_buy:
            stop_loss   = round(close - self.atr_stop_mult   * atr, 2)
            take_profit = round(close + self.atr_target_mult * atr, 2)
            risk        = close - stop_loss
            reward      = take_profit - close
            risk_reward = round(reward / risk, 2) if risk > 0 else None
        elif chart_sell:
            stop_loss   = round(close + self.atr_stop_mult   * atr, 2)
            take_profit = round(close - self.atr_target_mult * atr, 2)
            risk        = stop_loss - close
            reward      = close - take_profit
            risk_reward = round(reward / risk, 2) if risk > 0 else None

        return Signal(
            date=str(df_ind.index[-1].date()), ticker=ticker,
            close=round(close, 2),
            sma_fast=round(sma_fast, 2), sma_slow=round(sma_slow, 2),
            rsi=round(rsi, 2), atr=round(atr, 2),
            vol_oscillator=round(vol_osc, 2),
            macd=round(macd_val, 4), macd_signal=round(macd_sig, 4),
            macd_histogram=round(macd_hist, 4),
            bb_upper=round(bb_upper, 2), bb_middle=round(bb_middle, 2),
            bb_lower=round(bb_lower, 2), bb_pband=round(bb_pband, 4),
            stoch_k=round(stoch_k, 2), stoch_d=round(stoch_d, 2),
            adx=round(adx, 2), mfi=round(mfi, 2),
            obv_slope=round(obv_now - obv_sma, 0),
            golden_cross=golden_cross, rsi_ok=rsi_ok, volume_ok=volume_ok,
            macd_bullish=macd_bullish, bb_not_upper=bb_not_upper,
            stoch_not_over=stoch_not_over,
            adx_trending=adx_trending, mfi_ok=mfi_ok, obv_rising=obv_rising,
            chart_buy=chart_buy, chart_sell=chart_sell,
            death_cross=death_cross, rsi_oversold=rsi_overbought_f,
            macd_bearish=macd_bearish, bb_at_upper=bb_at_upper,
            stoch_overbought=stoch_overbought,
            weekly_trend_aligned=weekly_aligned, weekly_sma_cross=weekly_cross,
            stop_loss=stop_loss, take_profit=take_profit,
            risk_reward=risk_reward, trend_score=trend_score,
            kelly_fraction=kelly_f, fibonacci=fibonacci,
            earnings_date=earnings_date, earnings_warning=earnings_warning,
        )


# ════════════════════════════════════════════════════════════════════════════
# SENTIMENT ANALYZER
# ════════════════════════════════════════════════════════════════════════════

class SentimentAnalyzer:
    def __init__(self, provider: BaseLLMProvider, decay_rate: float = 0.5):
        self.provider   = provider
        self.decay_rate = decay_rate

    def fetch_news(self, ticker: str, n: int = 5) -> list[NewsItem]:
        stock = yf.Ticker(ticker)
        items = []
        for raw in stock.news[:n]:
            content   = raw.get("content", {})
            title     = content.get("title",   raw.get("title",   "N/A"))
            summary   = content.get("summary", raw.get("summary", ""))
            link      = (content.get("canonicalUrl", {}) or {}).get(
                "url", raw.get("link", "")
            )
            source    = (content.get("provider", {}) or {}).get(
                "displayName", raw.get("publisher", "Unknown")
            )
            pub_date  = content.get("pubDate", raw.get("providerPublishTime", ""))
            if isinstance(pub_date, (int, float)):
                pub_date = datetime.fromtimestamp(pub_date).strftime("%Y-%m-%d %H:%M")
            elif isinstance(pub_date, str) and pub_date:
                try:
                    pub_date = datetime.fromisoformat(
                        pub_date.replace("Z", "+00:00")
                    ).strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    pass
            items.append(NewsItem(
                title=title, summary=summary, link=link,
                source=source, published=pub_date,
            ))
        return items

    def score_one(self, item: NewsItem, ticker: str) -> float:
        info = TickerCache.get_info(ticker)  # 캐시 사용!
        company_name = info.get("shortName", ticker)
        prompt = (
            f"너는 월스트리트의 시니어 퀀트 애널리스트야. "
            f"다음 {company_name}({ticker}) 뉴스 헤드라인과 요약을 읽고, "
            f"단기 주가에 미칠 영향을 -1.0(매우 부정)에서 1.0(매우 긍정) 사이의 "
            f"숫자(float)로만 대답해. 다른 설명은 절대 하지 마.\n\n"
            f"뉴스:\n{item.title}\n{item.summary}"
        )
        raw   = self.provider.complete(prompt)
        match = re.search(r"-?\d+\.?\d*", raw)
        if match:
            return round(max(-1.0, min(1.0, float(match.group()))), 4)
        print(f"  [⚠ 파싱 실패] 모델 응답: '{raw}' → 0.0 으로 대체")
        return 0.0

    def analyze(self, ticker: str, n: int = 5) -> tuple[list[NewsItem], float]:
        items = self.fetch_news(ticker, n)
        for i, item in enumerate(items):
            item.sentiment_score = self.score_one(item, ticker)
            item.weight          = round(math.exp(-self.decay_rate * i), 4)

        total_w      = sum(it.weight for it in items)
        weighted_avg = (
            sum(it.weight * it.sentiment_score for it in items) / total_w
            if total_w > 0 else 0.0
        )
        return items, round(weighted_avg, 4)


# ════════════════════════════════════════════════════════════════════════════
# QUANT ANALYSIS ENGINE
# ════════════════════════════════════════════════════════════════════════════

class QuantAnalyst:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    def get_sector_info(self, ticker: str) -> str:
        info = TickerCache.get_info(ticker)
        sector     = info.get("sector",   "N/A")
        industry   = info.get("industry", "N/A")
        mkt_cap    = info.get("marketCap", 0)
        pe_ratio   = info.get("trailingPE", "N/A")
        fwd_pe     = info.get("forwardPE", "N/A")
        div_yield  = info.get("dividendYield", 0)
        beta       = info.get("beta", "N/A")
        w52_high   = info.get("fiftyTwoWeekHigh", "N/A")
        w52_low    = info.get("fiftyTwoWeekLow", "N/A")
        short_name = info.get("shortName", ticker)
        short_pct  = info.get("shortPercentOfFloat", 0)

        if isinstance(mkt_cap, (int, float)) and mkt_cap > 0:
            mkt_str = (f"${mkt_cap/1e12:.2f}T" if mkt_cap >= 1e12
                       else f"${mkt_cap/1e9:.2f}B" if mkt_cap >= 1e9
                       else f"${mkt_cap/1e6:.0f}M")
        else:
            mkt_str = "N/A"

        div_str   = f"{div_yield*100:.2f}%" if isinstance(div_yield, (int, float)) and div_yield else "없음"
        short_str = f"{short_pct*100:.1f}%" if isinstance(short_pct, (int, float)) and short_pct else "N/A"

        return (
            f"  회사명       : {short_name}\n"
            f"  섹터/산업    : {sector} / {industry}\n"
            f"  시가총액     : {mkt_str}\n"
            f"  P/E (TTM)    : {pe_ratio}   |  Forward P/E : {fwd_pe}\n"
            f"  배당수익률   : {div_str}\n"
            f"  Beta         : {beta}\n"
            f"  공매도 비율  : {short_str}\n"
            f"  52주 범위    : ${w52_low} — ${w52_high}"
        )

    def generate_report(self, signal: Signal, news_items: list[NewsItem],
                        weighted_sentiment: float, sector_info: str,
                        market_regime: MarketRegime,
                        relative_strength: RelativeStrength) -> str:
        news_text = ""
        for i, item in enumerate(news_items):
            news_text += f"  {i+1}. [{item.source} | {item.published}] {item.title} (감성: {item.sentiment_score:+.2f})\n"

        fib = signal.fibonacci
        fib_text = ""
        if fib:
            fib_text = (
                f"52주 고가: ${fib.high_52w} / 52주 저가: ${fib.low_52w}\n"
                f"피보나치 레벨: 23.6%=${fib.level_236} | 38.2%=${fib.level_382} | "
                f"50%=${fib.level_500} | 61.8%=${fib.level_618} | 78.6%=${fib.level_786}\n"
                f"가장 가까운 지지선: {fib.nearest_support}\n"
                f"가장 가까운 저항선: {fib.nearest_resist}"
            )

        prompt = f"""너는 20년 경력의 월스트리트 시니어 퀀트 트레이더야.
아래 데이터를 기반으로 {signal.ticker}에 대한 종합 트레이딩 분석 리포트를 한국어로 작성해.

═══ 기업 정보 ═══
{sector_info}

═══ 시장 환경 (Market Regime) ═══
VIX: {market_regime.vix_current} (SMA20: {market_regime.vix_sma20}) → {market_regime.regime_label}
SPY 추세: {market_regime.spy_trend} | SPY RSI: {market_regime.spy_rsi} | SPY 1개월 수익률: {market_regime.spy_change_1m:+.2f}%

═══ 상대강도 (vs SPY) ═══
{signal.ticker} 1개월: {relative_strength.ticker_return_1m:+.2f}% / 3개월: {relative_strength.ticker_return_3m:+.2f}%
SPY 1개월: {relative_strength.spy_return_1m:+.2f}% / 3개월: {relative_strength.spy_return_3m:+.2f}%
상대강도 차이: 1개월 {relative_strength.rs_ratio_1m:+.2f}%p / 3개월 {relative_strength.rs_ratio_3m:+.2f}%p
→ {'아웃퍼폼 (시장 대비 강세)' if relative_strength.outperforming else '언더퍼폼 (시장 대비 약세)'}

═══ 기술적 지표 ({signal.date}) ═══
종가: ${signal.close}
SMA50: {signal.sma_fast} / SMA200: {signal.sma_slow} → {'골든크로스' if signal.golden_cross else '데드크로스'}
주봉 추세: {signal.weekly_sma_cross} ({'일봉과 일치 ✅' if signal.weekly_trend_aligned else '일봉과 불일치 ⚠️'})
RSI(14): {signal.rsi} | ADX: {signal.adx} ({'추세 존재' if signal.adx_trending else '횡보/추세 약함'})
MACD: {signal.macd:.4f} / Signal: {signal.macd_signal:.4f} / Hist: {signal.macd_histogram:.4f}
볼린저밴드: ${signal.bb_lower} — ${signal.bb_middle} — ${signal.bb_upper} (%B: {signal.bb_pband:.2%})
스토캐스틱: %K={signal.stoch_k:.1f} / %D={signal.stoch_d:.1f}
MFI: {signal.mfi:.1f} | OBV 추세: {'상승 📈' if signal.obv_rising else '하락 📉'}
ATR(14): {signal.atr} ({signal.atr/signal.close*100:.2f}% 변동성)
거래량 오실레이터: {signal.vol_oscillator:+.2f}%
추세강도 점수: {signal.trend_score}/100

═══ 피보나치 되돌림 ═══
{fib_text}

═══ 포지션 사이징 ═══
Kelly Criterion 추천 비율: 포트폴리오의 {signal.kelly_fraction:.1f}%
{f'⚠️ 실적발표: {signal.earnings_date} — {signal.earnings_warning}' if signal.earnings_warning else '실적발표 임박 없음'}

═══ 뉴스 감성 분석 ═══
가중평균 감성: {weighted_sentiment:+.4f}
{news_text}

═══ 분석 요청 ═══
다음 항목을 포함해서 작성해:
1. [시장 환경] VIX 레짐과 SPY 흐름에서 현재 매매 환경이 유리한지
2. [상대강도] SPY 대비 이 종목이 아웃/언더퍼폼 중인 이유와 의미
3. [기술적 분석] 10개 지표 수렴/발산 분석 — 특히 ADX+MACD+볼린저 조합, 주봉 정렬 여부
4. [자금 흐름] MFI와 OBV가 보여주는 스마트머니 동향
5. [피보나치] 현재가가 피보나치 레벨 대비 어디인지, 진입 가격대 추천
6. [뉴스 해석] 뉴스가 주가에 미칠 영향과 시장 선반영 여부
7. [리스크 요인] 핵심 리스크 3가지 (실적, 매크로, 기술적)
8. [트레이딩 전략] 구체적 진입/청산 전략 + Kelly 기준 포지션 사이징
9. [결론] 1줄 요약 (STRONG BUY / BUY / HOLD / SELL / STRONG SELL + 이유)

간결하되 전문적으로, 실전 트레이더가 바로 참고할 수 있게 작성해."""

        return self.provider.complete_long(prompt)


# ════════════════════════════════════════════════════════════════════════════
# EXECUTION ENGINE
# ════════════════════════════════════════════════════════════════════════════

class ExecutionEngine:
    SENTIMENT_BUY_THRESHOLD  =  0.2
    SENTIMENT_SELL_THRESHOLD = -0.2

    def __init__(
        self,
        signal_gen : SignalGenerator,
        sentiment  : SentimentAnalyzer,
        analyst    : QuantAnalyst,
        ticker     : str = "AAPL",
    ):
        self.signal_gen = signal_gen
        self.sentiment  = sentiment
        self.analyst    = analyst
        self.ticker     = ticker

    def _download(self) -> pd.DataFrame:
        df = yf.download(
            self.ticker, period="1y", interval="1d",
            auto_adjust=True, progress=False,
        )
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        return df

    def _decide(self, signal: Signal, weighted_sentiment: float,
                market_regime: MarketRegime) -> str:
        # Extreme fear regime → more conservative
        regime_penalty = market_regime.regime in ("HIGH_VOL", "EXTREME_FEAR")

        if signal.chart_buy and weighted_sentiment > self.SENTIMENT_BUY_THRESHOLD:
            if regime_penalty:
                return "📈  BUY (매수) — ⚠️ 변동성 주의, 사이즈 축소 권장"
            return "✅  STRONG BUY  (강력 매수)"
        if signal.chart_sell and weighted_sentiment < self.SENTIMENT_SELL_THRESHOLD:
            return "🔻  STRONG SELL  (강력 매도)"
        if signal.trend_score >= 67 and weighted_sentiment > 0:
            return "📈  LEAN BUY  (매수 우위)"
        if signal.trend_score <= 33 and weighted_sentiment < 0:
            return "📉  LEAN SELL  (매도 우위)"
        return "⏳  WAIT  (관망)"

    def run(self) -> TradingDecision:
        print(f"\n📊 [1/5] {self.ticker} 데이터 다운로드 & 기술적 지표 계산 중 …")
        df     = self._download()
        signal = self.signal_gen.generate(self.ticker, df)
        rs     = self.signal_gen._compute_relative_strength(self.ticker, df)

        print(f"📰 [2/5] 뉴스 수집 & AI 감성 스코어링 ({self.sentiment.provider.label}) …")
        news_items, weighted_sentiment = self.sentiment.analyze(self.ticker)

        print(f"🌍 [3/5] 시장 환경 분석 (VIX + SPY) …")
        market_regime = MarketRegimeDetector.detect()

        print(f"🏢 [4/5] 기업/섹터 정보 조회 중 …")
        sector_info = self.analyst.get_sector_info(self.ticker)

        print(f"🧠 [5/5] 시니어 퀀트 종합 분석 생성 중 …\n")
        quant_analysis = self.analyst.generate_report(
            signal, news_items, weighted_sentiment,
            sector_info, market_regime, rs,
        )

        final_action = self._decide(signal, weighted_sentiment, market_regime)

        return TradingDecision(
            signal=signal, news_items=news_items,
            weighted_sentiment=weighted_sentiment,
            final_action=final_action,
            quant_analysis=quant_analysis,
            sector_info=sector_info,
            market_regime=market_regime,
            relative_strength=rs,
        )

    def print_report(self, d: TradingDecision) -> None:
        SEP  = "═" * 72
        THIN = "─" * 68
        sig  = d.signal

        print(f"\n{SEP}")
        print(f"  US QUANT TRADING BOT  ▸  {self.ticker}")
        print(f"  Senior Quant Edition v3  │  {sig.date}")
        print(f"{SEP}")

        # ── Block 0: Market Regime ──
        mr = d.market_regime
        if mr:
            print(f"\n  🌍  시장 환경 (Market Regime)")
            print(f"  {THIN}")
            print(f"  VIX          : {mr.vix_current:>6.2f}  (SMA20: {mr.vix_sma20:.2f})")
            print(f"  시장 레짐    : {mr.regime_label}")
            print(f"  SPY 추세     : {mr.spy_trend}  │  RSI: {mr.spy_rsi}  │  1M: {mr.spy_change_1m:+.2f}%")

        # ── Block 0.5: Relative Strength ──
        rs = d.relative_strength
        if rs:
            emo = "💪" if rs.outperforming else "⚠️"
            print(f"\n  {emo}  상대강도 (vs SPY)")
            print(f"  {THIN}")
            print(f"  {self.ticker:>6} :  1M {rs.ticker_return_1m:>+7.2f}%  │  3M {rs.ticker_return_3m:>+7.2f}%")
            print(f"  {'SPY':>6} :  1M {rs.spy_return_1m:>+7.2f}%  │  3M {rs.spy_return_3m:>+7.2f}%")
            print(f"  차이   :  1M {rs.rs_ratio_1m:>+7.2f}%p │  3M {rs.rs_ratio_3m:>+7.2f}%p"
                  f"  → {'아웃퍼폼 ✅' if rs.outperforming else '언더퍼폼 ❌'}")

        # ── Block 1: Company ──
        print(f"\n  🏢  기업 / 섹터 정보")
        print(f"  {THIN}")
        print(d.sector_info)

        # ── Block 1.5: Earnings Warning ──
        if sig.earnings_warning:
            print(f"\n  📅  실적발표 경고")
            print(f"  {THIN}")
            print(f"  {sig.earnings_warning}")
            print(f"  실적발표일: {sig.earnings_date}")

        # ── Block 2: News ──
        print(f"\n  📰  뉴스 감성 분석  (Time-Decay λ={self.sentiment.decay_rate})")
        print(f"  {THIN}")

        for i, item in enumerate(d.news_items):
            s     = item.sentiment_score
            label = "▲ BULL" if s > 0.2 else ("▼ BEAR" if s < -0.2 else "◆ NEUT")
            short = item.summary[:100] + ("…" if len(item.summary) > 100 else "")
            src   = f"[{item.source}]" if item.source else ""
            pub   = f" {item.published}" if item.published else ""
            print(f"\n  [{i+1}] {item.title}")
            print(f"       {src}{pub}")
            if short:
                print(f"       {short}")
            print(f"       Score {s:+.4f}  │  Weight {item.weight:.4f}  │  {label}")

        ws       = d.weighted_sentiment
        ws_label = "Bullish" if ws > 0.2 else "Bearish" if ws < -0.2 else "Neutral"
        print(f"\n  {THIN}")
        print(f"  가중평균 감성 : {ws:+.4f}  ({ws_label})")

        # ── Block 3: Multi-Factor Chart ──
        print(f"\n  📊  10-Factor 차트 시그널  ({sig.date})")
        print(f"  {THIN}")

        def row(lbl, val, ok, note=""):
            print(f"  {'✅' if ok else '❌'}  {lbl:<36} {val:<24} {note}")

        print(f"  {'─'*8} 코어 매수 조건 (3/3 필수) {'─'*35}")
        row("Golden Cross  (SMA50 > SMA200)",
            f"SMA50 {sig.sma_fast:>7.2f} / SMA200 {sig.sma_slow:>7.2f}", sig.golden_cross)
        row(f"RSI 과매수 아님  (< {self.signal_gen.rsi_overbought:.0f})",
            f"RSI = {sig.rsi:>6.2f}", sig.rsi_ok)
        row("거래량 확인  (VO > 0%)",
            f"VO = {sig.vol_oscillator:>+7.2f}%", sig.volume_ok)

        print(f"\n  {'─'*8} 확장 지표 (2/3 이상) {'─'*40}")
        row("MACD 불리시  (MACD > Signal)",
            f"MACD {sig.macd:>+.4f}", sig.macd_bullish)
        row("볼린저 밴드  (%B < 95%)",
            f"%B = {sig.bb_pband:.2%}", sig.bb_not_upper)
        row("스토캐스틱  (%K < 80)",
            f"%K={sig.stoch_k:.1f} / %D={sig.stoch_d:.1f}", sig.stoch_not_over)

        print(f"\n  {'─'*8} 고급 지표 (2/3 이상) {'─'*40}")
        row(f"ADX 추세 확인  (> 25)",
            f"ADX = {sig.adx:>6.2f}", sig.adx_trending,
            "추세 존재" if sig.adx_trending else "횡보/약추세")
        row("MFI 과매수 아님  (< 80)",
            f"MFI = {sig.mfi:>6.2f}", sig.mfi_ok)
        row("OBV 상승  (자금 유입)",
            f"OBV Δ = {sig.obv_slope:>+,.0f}", sig.obv_rising)

        # Multi-timeframe
        wk_icon = "✅" if sig.weekly_trend_aligned else "⚠️"
        print(f"\n  {'─'*8} 멀티타임프레임 {'─'*44}")
        print(f"  {wk_icon}  주봉 추세 : {sig.weekly_sma_cross}"
              f"  {'(일봉과 일치)' if sig.weekly_trend_aligned else '(일봉과 불일치 — 매수 차단)'}")

        if sig.chart_sell or (not sig.chart_buy and sig.death_cross):
            print(f"\n  {'─'*8} 매도 조건 {'─'*48}")
            row("Death Cross  (SMA50 < SMA200)", f"", sig.death_cross)
            row("RSI 과매수  (> 70)", f"RSI = {sig.rsi:.2f}", sig.rsi_oversold)
            row("MACD 베어리시", f"MACD {sig.macd:>+.4f}", sig.macd_bearish)
            row("볼린저 상단 터치  (%B > 95%)", f"%B = {sig.bb_pband:.2%}", sig.bb_at_upper)
            row("스토캐스틱 과매수  (%K > 80)", f"%K = {sig.stoch_k:.1f}", sig.stoch_overbought)

        # ── Price & Fibonacci ──
        print(f"\n  종가         : ${sig.close:>8.2f}")
        print(f"  ATR ({self.signal_gen.atr_period:>2}d)    :  {sig.atr:>8.2f}"
              f"   ({sig.atr / sig.close * 100:.2f}% 변동성)")
        print(f"  볼린저 밴드  :  ${sig.bb_lower:.2f} — ${sig.bb_middle:.2f} — ${sig.bb_upper:.2f}")

        if sig.fibonacci:
            fib = sig.fibonacci
            print(f"\n  📐  피보나치 되돌림 레벨 (52주 기준)")
            print(f"  {THIN}")
            print(f"  52주 고가  ${fib.high_52w:>8.2f}  ────────────── 100%")
            print(f"  23.6%      ${fib.level_236:>8.2f}")
            print(f"  38.2%      ${fib.level_382:>8.2f}")
            print(f"  50.0%      ${fib.level_500:>8.2f}")
            print(f"  61.8%      ${fib.level_618:>8.2f}")
            print(f"  78.6%      ${fib.level_786:>8.2f}")
            print(f"  52주 저가  ${fib.low_52w:>8.2f}  ──────────────   0%")
            print(f"  현재가     ${sig.close:>8.2f}  ◄━━")
            print(f"  가까운 지지 : {fib.nearest_support}")
            print(f"  가까운 저항 : {fib.nearest_resist}")

        print(f"\n  추세강도     :  {sig.trend_score}/100"
              f"  {'█' * (sig.trend_score // 5)}{'░' * (20 - sig.trend_score // 5)}")

        # ── Block 4: Risk Management ──
        if sig.stop_loss is not None:
            direction = "매수" if sig.chart_buy else "매도(숏)"
            stop_pct   = (sig.stop_loss   - sig.close) / sig.close * 100
            target_pct = (sig.take_profit - sig.close) / sig.close * 100

            print(f"\n  🛡  리스크 관리  ({direction})")
            print(f"  {THIN}")
            print(f"  진입가 (현재 종가)   : ${sig.close:>8.2f}")
            print(f"  손절라인 (Stop-Loss) : ${sig.stop_loss:>8.2f}   ({stop_pct:+.2f}%)")
            print(f"  익절라인 (Target)    : ${sig.take_profit:>8.2f}   ({target_pct:+.2f}%)")
            print(f"  리스크/리워드 비율   :   {sig.risk_reward:.2f} : 1")
            print(f"  Kelly 추천 포지션    :   포트폴리오의 {sig.kelly_fraction:.1f}%")

        # ── Block 5: Final Decision ──
        buy_met = sum([
            sig.golden_cross, sig.rsi_ok, sig.volume_ok,
            sig.macd_bullish, sig.bb_not_upper, sig.stoch_not_over,
            sig.adx_trending, sig.mfi_ok, sig.obv_rising,
        ])
        sentiment_pass = d.weighted_sentiment > self.SENTIMENT_BUY_THRESHOLD

        print(f"\n{SEP}")
        print(f"  🎯  최종 판단")
        print(f"  {THIN}")
        print(f"  매수 조건 충족      :  {buy_met} / 9")
        print(f"  주봉 정렬           :  {'✅' if sig.weekly_trend_aligned else '❌'}")
        print(f"  시장 레짐           :  {d.market_regime.regime_label if d.market_regime else 'N/A'}")
        print(f"  상대강도 (vs SPY)   :  "
              f"{'아웃퍼폼 ✅' if d.relative_strength and d.relative_strength.outperforming else '언더퍼폼 ❌'}")
        print(f"  감성 분석           :  "
              f"{'PASS ✅' if sentiment_pass else 'FAIL ❌'}"
              f"  ({d.weighted_sentiment:+.4f})")
        print(f"  추세강도            :  {sig.trend_score}/100")
        if sig.earnings_warning:
            print(f"  ⚠️  {sig.earnings_warning}")
        print(f"  {THIN}")
        print(f"  ▶  {d.final_action}")
        print(f"{SEP}")

        # ── Block 6: Quant Report ──
        if d.quant_analysis:
            print(f"\n  🧠  시니어 퀀트 트레이더 종합 분석")
            print(f"  {THIN}")
            for line in d.quant_analysis.split("\n"):
                print(f"  {line}")
            print(f"  {THIN}")

        print(f"\n  Strategy : 10-Factor + MTF + {self.sentiment.provider.label} + VIX Regime + Kelly")
        print(f"  Risk     : {self.signal_gen.atr_stop_mult:.0f}×ATR Stop"
              f"  │  {self.signal_gen.atr_target_mult:.0f}×ATR Target"
              f"  │  {self.signal_gen.atr_target_mult / self.signal_gen.atr_stop_mult:.1f}:1 R/R\n")


# ════════════════════════════════════════════════════════════════════════════
# INTERACTIVE MODE
# ════════════════════════════════════════════════════════════════════════════

def interactive_mode(provider: BaseLLMProvider):
    SEP = "═" * 72

    print(f"\n{SEP}")
    print(f"  US QUANT TRADING BOT  ▸  Interactive Mode  (v3)")
    print(f"  10-Factor │ Multi-Timeframe │ VIX Regime │ Kelly Sizing")
    print(f"{SEP}")
    print(f"\n  사용법:")
    print(f"    종목 티커를 입력하세요 (예: AAPL, TSLA, NVDA, MSFT)")
    print(f"    'q' 또는 'quit' 를 입력하면 종료합니다.")
    print(f"    'help' 를 입력하면 인기 종목 목록을 보여줍니다.")
    print(f"    'vix' 를 입력하면 현재 시장 환경만 확인합니다.\n")

    POPULAR = {
        "기술":    ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
        "반도체":  ["NVDA", "AMD", "INTC", "TSM", "AVGO", "QCOM", "MU"],
        "금융":    ["JPM", "BAC", "GS", "MS", "V", "MA"],
        "헬스케어": ["JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY"],
        "에너지":  ["XOM", "CVX", "COP", "SLB", "EOG"],
        "ETF":     ["SPY", "QQQ", "IWM", "DIA", "ARKK", "SOXX"],
        "암호화폐": ["COIN", "MARA", "RIOT", "MSTR"],
    }

    signal_gen = SignalGenerator()
    sentiment  = SentimentAnalyzer(provider=provider, decay_rate=0.5)
    analyst    = QuantAnalyst(provider=provider)

    while True:
        try:
            ticker = input("\n  📎 종목 티커 입력 > ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  종료합니다. 좋은 트레이딩 되세요! 🚀\n")
            break

        if ticker in ("Q", "QUIT", "EXIT"):
            print("\n  종료합니다. 좋은 트레이딩 되세요! 🚀\n")
            break

        if ticker == "HELP":
            print(f"\n  {'─'*60}")
            for cat, tickers in POPULAR.items():
                print(f"  {cat:>8} : {', '.join(tickers)}")
            print(f"  {'─'*60}")
            continue

        if ticker == "VIX":
            print("\n  🌍  시장 환경 조회 중 …")
            try:
                mr = MarketRegimeDetector.detect()
                print(f"  VIX: {mr.vix_current} (SMA20: {mr.vix_sma20})")
                print(f"  레짐: {mr.regime_label}")
                print(f"  SPY: {mr.spy_trend} │ RSI: {mr.spy_rsi} │ 1M: {mr.spy_change_1m:+.2f}%")
            except Exception as e:
                print(f"  ❌  오류: {e}")
            continue

        if not ticker:
            continue

        # Validate
        try:
            info = TickerCache.get_info(ticker)
            if not info or info.get("regularMarketPrice") is None:
                print(f"  ❌  '{ticker}' 는 유효하지 않은 티커입니다.")
                continue
        except Exception:
            print(f"  ❌  '{ticker}' 조회 실패.")
            continue

        print(f"\n  ✅  {ticker} 종합 분석을 시작합니다…")
        try:
            engine = ExecutionEngine(
                signal_gen=signal_gen, sentiment=sentiment,
                analyst=analyst, ticker=ticker,
            )
            decision = engine.run()
            engine.print_report(decision)
        except Exception as e:
            print(f"\n  ❌  분석 중 오류: {e}")
            import traceback; traceback.print_exc()


# ════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    SEP = "═" * 72
    print(f"\n{SEP}")
    print(f"  US QUANT TRADING BOT  ▸  Initialising …  (v3)")
    print(f"  10-Factor │ Multi-Timeframe │ VIX Regime │ Kelly Sizing")
    print(f"{SEP}\n")

    # ── LLM Provider ──
    provider = OllamaProvider(model="llama3")
    # provider = AnthropicProvider()

    # ── Mode ──
    print(f"  모드를 선택하세요:")
    print(f"    1) 인터랙티브 모드 — 원하는 종목 직접 입력")
    print(f"    2) 단일 실행 모드 — 기본 종목(AAPL) 분석")
    print()

    try:
        choice = input("  선택 (1/2, 기본=1) > ").strip()
    except (EOFError, KeyboardInterrupt):
        choice = "1"

    if choice == "2":
        engine = ExecutionEngine(
            signal_gen=SignalGenerator(),
            sentiment=SentimentAnalyzer(provider=provider, decay_rate=0.5),
            analyst=QuantAnalyst(provider=provider),
            ticker="AAPL",
        )
        decision = engine.run()
        engine.print_report(decision)
    else:
        interactive_mode(provider)

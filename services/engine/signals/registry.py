"""100 named signal analyzers — ensemble stubs (not 100 LLM calls)."""
from __future__ import annotations
import hashlib
import math
from dataclasses import dataclass
from typing import List

SIGNAL_NAMES = ['SMA_Cross_9_21', 'EMA_Cross_12_26', 'MACD_Histogram', 'ADX_Trend_Strength', 'Ichimoku_Cloud', 'Parabolic_SAR', 'SuperTrend', 'Donchian_Breakout', 'Hull_MA_Slope', 'TEMA_Direction', 'KAMA_Adaptive', 'ALMA_Trend', 'Vortex_Indicator', 'Aroon_UpDown', 'Linear_Reg_Slope', 'RSI_14', 'RSI_Divergence', 'Stochastic_K_D', 'CCI_20', 'Williams_R', 'ROC_12', 'Momentum_10', 'TSI_TrueStrength', 'Ultimate_Oscillator', 'Awesome_Oscillator', 'CMO_Chande', 'PPO_PercentPrice', 'DPO_Detrended', 'Connors_RSI', 'StochRSI', 'ATR_Expansion', 'Bollinger_Squeeze', 'Bollinger_PercentB', 'Keltner_Channel', 'Historical_Vol_20', 'Parkinson_Vol', 'Garman_Klass_Vol', 'Chaikin_Vol', 'Ulcer_Index', 'StdDev_Bands', 'HV_Rank', 'Vol_Regime_HMM_Stub', 'OBV_Slope', 'VWAP_Deviation', 'CVD_CumulativeDelta', 'Volume_Spike', 'MFI_MoneyFlow', 'Chaikin_MoneyFlow', 'Ease_Of_Movement', 'Force_Index', 'Volume_Profile_POC', 'Relative_Volume', 'Accumulation_Dist', 'Klinger_Osc', 'OB_Imbalance_L1', 'OB_Imbalance_L5', 'Bid_Ask_Spread', 'Depth_Ratio_1pct', 'Book_Pressure', 'Wall_Detect_Bid', 'Wall_Detect_Ask', 'Microprice_Bias', 'Trade_Flow_Toxicity', 'Cancel_Rate_Proxy', 'Funding_Rate_Bias', 'Funding_Extreme', 'Open_Interest_Delta', 'OI_Price_Div', 'Long_Short_Ratio', 'Top_Trader_LS', 'Liquidation_Cluster_Long', 'Liquidation_Cluster_Short', 'Perp_Basis', 'Quarterly_Basis', 'BTC_Lead_Lag', 'ETH_Beta', 'BTC_Correlation_1h', 'Alt_BTC_Strength', 'Sector_Rotation_Stub', 'Stablecoin_Dominance', 'DXY_Proxy_Stub', 'Gold_Correlation_Stub', 'SPX_Risk_On_Stub', 'Cross_Asset_Momentum', 'Binance_Coinbase_Premium', 'Korea_Premium_Stub', 'Spot_Perp_Premium', 'USDT_Premium', 'Stable_Peg_Stress', 'Exchange_Inflow_Stub', 'News_Keyword_Bull', 'News_Keyword_Bear', 'Social_Volume_Stub', 'Fear_Greed_Proxy', 'Whale_Alert_Stub', 'ETF_Flow_Stub', 'Asia_Session_Bias', 'US_Open_Volatility', 'Weekend_Liquidity', 'Month_End_Effect']
SIGNAL_CATEGORIES = ['trend', 'trend', 'trend', 'trend', 'trend', 'trend', 'trend', 'trend', 'trend', 'trend', 'trend', 'trend', 'trend', 'trend', 'trend', 'momentum', 'momentum', 'momentum', 'momentum', 'momentum', 'momentum', 'momentum', 'momentum', 'momentum', 'momentum', 'momentum', 'momentum', 'momentum', 'momentum', 'momentum', 'volatility', 'volatility', 'volatility', 'volatility', 'volatility', 'volatility', 'volatility', 'volatility', 'volatility', 'volatility', 'volatility', 'volatility', 'volume', 'volume', 'volume', 'volume', 'volume', 'volume', 'volume', 'volume', 'volume', 'volume', 'volume', 'volume', 'orderbook', 'orderbook', 'orderbook', 'orderbook', 'orderbook', 'orderbook', 'orderbook', 'orderbook', 'orderbook', 'orderbook', 'funding_oi', 'funding_oi', 'funding_oi', 'funding_oi', 'funding_oi', 'funding_oi', 'funding_oi', 'funding_oi', 'funding_oi', 'funding_oi', 'correlation', 'correlation', 'correlation', 'correlation', 'correlation', 'correlation', 'correlation', 'correlation', 'correlation', 'correlation', 'cross_exchange', 'cross_exchange', 'cross_exchange', 'cross_exchange', 'cross_exchange', 'cross_exchange', 'news_sentiment', 'news_sentiment', 'news_sentiment', 'news_sentiment', 'news_sentiment', 'news_sentiment', 'session', 'session', 'session', 'session']

@dataclass
class SignalResult:
    id: int
    name: str
    category: str
    score: float  # -100 .. +100
    confidence: float  # 0 .. 1
    note: str

def _seed_score(name: str, symbol: str, ts: float) -> float:
    """Deterministic pseudo-score from symbol+name+time bucket."""
    bucket = int(ts // 15)  # change every ~15s
    h = hashlib.sha256(f"{name}:{symbol}:{bucket}".encode()).hexdigest()
    raw = int(h[:8], 16) / 0xFFFFFFFF
    # smooth-ish wave + noise
    wave = math.sin(raw * math.pi * 2 + bucket * 0.1)
    score = max(-100.0, min(100.0, wave * 80 + (raw - 0.5) * 40))
    return round(score, 2)

def evaluate_all(symbol: str, ts: float) -> List[SignalResult]:
    out: List[SignalResult] = []
    for i, (name, cat) in enumerate(zip(SIGNAL_NAMES, SIGNAL_CATEGORIES), start=1):
        score = _seed_score(name, symbol, ts)
        conf = round(0.4 + abs(score) / 200, 3)
        bias = "bullish" if score > 15 else ("bearish" if score < -15 else "neutral")
        out.append(SignalResult(
            id=i, name=name, category=cat, score=score,
            confidence=min(1.0, conf), note=f"mock {bias}",
        ))
    return out

def consensus(results: List[SignalResult]) -> dict:
    if not results:
        return {"score": 0.0, "bullish": 0, "bearish": 0, "neutral": 0, "action": "hold"}
    wsum = sum(r.score * r.confidence for r in results)
    w = sum(r.confidence for r in results) or 1.0
    score = round(wsum / w, 2)
    bull = sum(1 for r in results if r.score > 15)
    bear = sum(1 for r in results if r.score < -15)
    neut = len(results) - bull - bear
    action = "buy" if score >= 25 else ("sell" if score <= -25 else "hold")
    return {
        "score": score,
        "bullish": bull,
        "bearish": bear,
        "neutral": neut,
        "action": action,
    }

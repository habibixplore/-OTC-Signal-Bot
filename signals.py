import numpy as np
import pandas as pd
from collections import deque
from dataclasses import dataclass
from typing import Optional
import time

import config


@dataclass
class Signal:
    symbol: str
    direction: str
    confidence: float
    expiry: int
    price: float
    rsi: float
    reason: str
    timestamp: float


class SignalEngine:
    def __init__(self):
        self.ticks: dict[str, deque] = {
            sym: deque(maxlen=config.TICK_BUFFER_SIZE)
            for sym in config.OTC_SYMBOLS
        }
        self.last_signal_time: dict[str, float] = {}

    def add_tick(self, symbol: str, price: float) -> Optional[Signal]:
        """Store tick and auto-check for signal with cooldown."""
        if symbol not in self.ticks:
            return None
        self.ticks[symbol].append(price)

        if len(self.ticks[symbol]) < config.MIN_TICKS_FOR_SIGNAL:
            return None

        now = time.time()
        if now - self.last_signal_time.get(symbol, 0) < config.SIGNAL_COOLDOWN:
            return None

        signal = self._analyze(symbol, now)
        if signal:
            self.last_signal_time[symbol] = now
        return signal

    def analyze_now(self, symbol: str) -> Optional[Signal]:
        """Force analyze on demand — ignores cooldown."""
        if len(self.ticks.get(symbol, [])) < config.MIN_TICKS_FOR_SIGNAL:
            return None
        return self._analyze(symbol, time.time())

    def _analyze(self, symbol: str, now: float) -> Optional[Signal]:
        prices = np.array(self.ticks[symbol])
        series = pd.Series(prices)

        rsi = self._rsi(series)
        ema_fast = series.ewm(span=config.EMA_FAST, adjust=False).mean()
        ema_slow = series.ewm(span=config.EMA_SLOW, adjust=False).mean()
        bb_upper, bb_lower = self._bollinger(series)

        current_price = prices[-1]
        ef_now, ef_prev = ema_fast.iloc[-1], ema_fast.iloc[-2]
        es_now, es_prev = ema_slow.iloc[-1], ema_slow.iloc[-2]

        # ── CALL ──────────────────────────────────────────
        call_score, call_reasons = 0, []
        if rsi < config.RSI_OVERSOLD:
            call_score += 40
            call_reasons.append(f"RSI oversold ({rsi:.1f})")
        elif rsi < 45:
            call_score += 15
            call_reasons.append(f"RSI low ({rsi:.1f})")
        if ef_prev < es_prev and ef_now > es_now:
            call_score += 35
            call_reasons.append("Bullish EMA crossover")
        elif ef_now > es_now:
            call_score += 10
            call_reasons.append("EMA bullish")
        if current_price <= bb_lower:
            call_score += 25
            call_reasons.append("Price at BB lower")

        # ── PUT ───────────────────────────────────────────
        put_score, put_reasons = 0, []
        if rsi > config.RSI_OVERBOUGHT:
            put_score += 40
            put_reasons.append(f"RSI overbought ({rsi:.1f})")
        elif rsi > 55:
            put_score += 15
            put_reasons.append(f"RSI high ({rsi:.1f})")
        if ef_prev > es_prev and ef_now < es_now:
            put_score += 35
            put_reasons.append("Bearish EMA crossover")
        elif ef_now < es_now:
            put_score += 10
            put_reasons.append("EMA bearish")
        if current_price >= bb_upper:
            put_score += 25
            put_reasons.append("Price at BB upper")

        # Pick strongest
        if call_score >= put_score and call_score >= config.MIN_CONFIDENCE:
            return Signal(symbol=symbol, direction="CALL",
                          confidence=min(call_score, 95), expiry=config.DEFAULT_EXPIRY,
                          price=current_price, rsi=rsi,
                          reason=" + ".join(call_reasons), timestamp=now)
        elif put_score > call_score and put_score >= config.MIN_CONFIDENCE:
            return Signal(symbol=symbol, direction="PUT",
                          confidence=min(put_score, 95), expiry=config.DEFAULT_EXPIRY,
                          price=current_price, rsi=rsi,
                          reason=" + ".join(put_reasons), timestamp=now)
        return None

    def _rsi(self, series: pd.Series) -> float:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=config.RSI_PERIOD - 1, adjust=False).mean().iloc[-1]
        avg_loss = loss.ewm(com=config.RSI_PERIOD - 1, adjust=False).mean().iloc[-1]
        if avg_loss == 0:
            return 100.0
        return 100 - (100 / (1 + avg_gain / avg_loss))

    def _bollinger(self, series: pd.Series):
        rolling = series.rolling(window=config.BB_PERIOD)
        mean = rolling.mean().iloc[-1]
        std = rolling.std().iloc[-1]
        return mean + config.BB_STD * std, mean - config.BB_STD * std

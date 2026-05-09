import os
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

# ── Deriv ─────────────────────────────────────────────────
DERIV_APP_ID = os.getenv("DERIV_APP_ID", "1089")
DERIV_WS_URL = f"wss://ws.derivws.com/websockets/v3?app_id={DERIV_APP_ID}"

# ── OTC Symbols (weekend OTC market) ─────────────────────
OTC_SYMBOLS = [
    "frxEURUSD",
    "frxGBPUSD",
    "frxUSDJPY",
    "frxAUDUSD",
    "frxUSDCAD",
    "frxUSDCHF",
    "frxEURGBP",
    "frxEURJPY",
    "frxGBPJPY",
    "frxAUDJPY",
    "frxNZDUSD",
    "frxEURAUD",
]

SYMBOL_NAMES = {
    "frxEURUSD": "EUR/USD OTC",
    "frxGBPUSD": "GBP/USD OTC",
    "frxUSDJPY": "USD/JPY OTC",
    "frxAUDUSD": "AUD/USD OTC",
    "frxUSDCAD": "USD/CAD OTC",
    "frxUSDCHF": "USD/CHF OTC",
    "frxEURGBP": "EUR/GBP OTC",
    "frxEURJPY": "EUR/JPY OTC",
    "frxGBPJPY": "GBP/JPY OTC",
    "frxAUDJPY": "AUD/JPY OTC",
    "frxNZDUSD": "NZD/USD OTC",
    "frxEURAUD": "EUR/AUD OTC",
}

# ── Signal Settings ───────────────────────────────────────
TICK_BUFFER_SIZE = 100
MIN_TICKS_FOR_SIGNAL = 50

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

EMA_FAST = 9
EMA_SLOW = 21

BB_PERIOD = 20
BB_STD = 2

DEFAULT_EXPIRY = 3
MIN_CONFIDENCE = 60
SIGNAL_COOLDOWN = 120

import asyncio
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode

import config
from signals import Signal


CALL_EMOJI = "🟢"
PUT_EMOJI = "🔴"
FIRE_EMOJI = "🔥"
CLOCK_EMOJI = "⏰"
CHART_EMOJI = "📊"
TARGET_EMOJI = "🎯"


def confidence_bar(confidence: float) -> str:
    filled = int(confidence / 10)
    empty = 10 - filled
    return "█" * filled + "░" * empty


def format_signal(signal: Signal) -> str:
    name = config.SYMBOL_NAMES.get(signal.symbol, signal.symbol)
    direction_emoji = CALL_EMOJI if signal.direction == "CALL" else PUT_EMOJI
    direction_label = "⬆️ CALL" if signal.direction == "CALL" else "⬇️ PUT"
    bar = confidence_bar(signal.confidence)
    now_str = datetime.utcfromtimestamp(signal.timestamp).strftime("%H:%M:%S UTC")

    message = (
        f"{FIRE_EMOJI} *SIGNAL ALERT* {FIRE_EMOJI}\n"
        f"{'─' * 28}\n"
        f"{CHART_EMOJI} *Asset:* `{name}`\n"
        f"{direction_emoji} *Direction:* *{direction_label}*\n"
        f"{CLOCK_EMOJI} *Expiry:* `{signal.expiry} min`\n"
        f"{TARGET_EMOJI} *Entry Price:* `{signal.price:.5f}`\n"
        f"\n"
        f"📈 *RSI:* `{signal.rsi:.1f}`\n"
        f"💡 *Reason:* _{signal.reason}_\n"
        f"\n"
        f"🎯 *Confidence:*\n"
        f"`{bar}` {signal.confidence:.0f}%\n"
        f"{'─' * 28}\n"
        f"🕐 _{now_str}_\n"
        f"\n"
        f"⚠️ _Trade on Pocket Option. Always manage risk._"
    )
    return message


class TelegramNotifier:
    def __init__(self):
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        self.channel_id = config.TELEGRAM_CHANNEL_ID

    async def send_signal(self, signal: Signal):
        message = format_signal(signal)
        try:
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
            )
            print(f"[SENT] {signal.symbol} {signal.direction} {signal.confidence:.0f}%")
        except Exception as e:
            print(f"[ERROR] Telegram send failed: {e}")

    async def send_startup(self):
        pairs = "\n".join(f"  • {v}" for v in config.SYMBOL_NAMES.values())
        msg = (
            f"🤖 *Signal Bot Started*\n"
            f"{'─' * 28}\n"
            f"Monitoring *{len(config.OTC_SYMBOLS)}* OTC pairs:\n"
            f"{pairs}\n\n"
            f"Strategy: RSI + EMA Crossover + Bollinger Bands\n"
            f"Min confidence: {config.MIN_CONFIDENCE}%\n"
            f"Default expiry: {config.DEFAULT_EXPIRY} min\n"
            f"{'─' * 28}\n"
            f"_Signals will appear here in real time_ ✅"
        )
        try:
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=msg,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            print(f"[ERROR] Startup message failed: {e}")

import asyncio
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode

import config
from signals import Signal


def confidence_bar(confidence: float) -> str:
    filled = int(confidence / 10)
    empty = 10 - filled
    return "█" * filled + "░" * empty


def order_flow_bar(buy_pressure: float) -> str:
    """Visual bar showing buy vs sell pressure."""
    buy_blocks = int(buy_pressure / 10)
    sell_blocks = 10 - buy_blocks
    return f"🟢{'█' * buy_blocks}{'█' * sell_blocks}🔴"


def format_signal(signal: Signal) -> str:
    name = config.SYMBOL_NAMES.get(signal.symbol, signal.symbol)
    direction_emoji = "🟢" if signal.direction == "CALL" else "🔴"
    direction_label = "⬆️ CALL" if signal.direction == "CALL" else "⬇️ PUT"
    bar = confidence_bar(signal.confidence)
    sell_pressure = 100 - signal.order_flow
    now_str = datetime.utcfromtimestamp(signal.timestamp).strftime("%H:%M:%S UTC")

    message = (
        f"🔥 *SIGNAL ALERT* 🔥\n"
        f"{'━' * 26}\n"
        f"📊 *Asset:* `{name}`\n"
        f"{direction_emoji} *Direction:* *{direction_label}*\n"
        f"⏰ *Expiry:* `{signal.expiry} min`\n"
        f"🎯 *Entry:* `{signal.price:.5f}`\n"
        f"{'━' * 26}\n"
        f"📈 *RSI:* `{signal.rsi:.1f}`\n"
        f"📦 *Order Flow:*\n"
        f"   Buy `{signal.order_flow:.0f}%` vs Sell `{sell_pressure:.0f}%`\n"
        f"💥 *Momentum:* `{signal.momentum}`\n"
        f"💡 *Reason:* _{signal.reason}_\n"
        f"{'━' * 26}\n"
        f"🎯 *Confidence:*\n"
        f"`{bar}` {signal.confidence:.0f}%\n"
        f"{'━' * 26}\n"
        f"🕐 _{now_str}_\n\n"
        f"⚠️ _Trade on Pocket Option. Manage your risk._"
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
            print(f"[SENT] {signal.symbol} {signal.direction} {signal.confidence:.0f}% | Flow: {signal.order_flow:.0f}% buy")
        except Exception as e:
            print(f"[ERROR] Telegram send failed: {e}")

    async def send_startup(self):
        pairs = "\n".join(f"  • {v}" for v in config.SYMBOL_NAMES.values())
        msg = (
            f"🤖 *Signal Bot Started*\n"
            f"{'━' * 26}\n"
            f"Monitoring *{len(config.OTC_SYMBOLS)}* OTC pairs:\n"
            f"{pairs}\n\n"
            f"*Strategy:*\n"
            f"RSI + EMA Crossover\n"
            f"Bollinger Bands\n"
            f"Order Flow Analysis 📦\n\n"
            f"Min confidence: {config.MIN_CONFIDENCE}%\n"
            f"Default expiry: {config.DEFAULT_EXPIRY} min\n"
            f"{'━' * 26}\n"
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

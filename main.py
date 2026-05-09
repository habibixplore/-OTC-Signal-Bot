import asyncio
import sys
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes

import config
from deriv_client import DerivClient
from signals import SignalEngine
from notifier import TelegramNotifier, format_signal

engine = SignalEngine()
notifier = None
app = None


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"🤖 *OTC Precision Scalper Bot*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Auto signals drop here in real time\n"
        f"✅ Request any pair anytime\n\n"
        f"*Commands:*\n"
        f"`/signal eurusd` — get signal for EUR/USD OTC\n"
        f"`/signal gbpusd` — get signal for GBP/USD OTC\n"
        f"`/signal usdjpy` — get signal for USD/JPY OTC\n"
        f"`/pairs` — see all available OTC pairs\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_Trade on Pocket Option. Manage your risk!_ ⚠️"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pairs = "\n".join(
        f"`/signal {k.replace('frx','').replace('_OTC','').lower()}` — {v}"
        for k, v in config.SYMBOL_NAMES.items()
    )
    msg = f"📊 *Available OTC Pairs:*\n\n{pairs}"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Specify a pair.\nExample: `/signal eurusd`",
            parse_mode="Markdown"
        )
        return

    user_input = context.args[0].upper().replace("/", "").replace("-", "").replace(" ", "")

    matched_symbol = None
    for sym in config.OTC_SYMBOLS:
        clean = sym.replace("frx", "").replace("_OTC", "")
        if user_input == clean:
            matched_symbol = sym
            break

    if not matched_symbol:
        available = " | ".join(
            s.replace("frx", "").replace("_OTC", "").lower()
            for s in config.OTC_SYMBOLS
        )
        await update.message.reply_text(
            f"❌ Pair `{user_input}` not found.\n\nTry: `{available}`\n\nUse `/pairs` for full list.",
            parse_mode="Markdown"
        )
        return

    ticks = len(engine.ticks.get(matched_symbol, []))
    if ticks < config.MIN_TICKS_FOR_SIGNAL:
        needed = config.MIN_TICKS_FOR_SIGNAL - ticks
        await update.message.reply_text(
            f"⏳ Still collecting data for `{config.SYMBOL_NAMES[matched_symbol]}`\n"
            f"Need {needed} more ticks (~{needed}s). Try again shortly.",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        f"🔍 Analyzing `{config.SYMBOL_NAMES[matched_symbol]}`...",
        parse_mode="Markdown"
    )

    signal = engine.analyze_now(matched_symbol)

    if signal:
        msg = format_signal(signal)
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        name = config.SYMBOL_NAMES[matched_symbol]
        await update.message.reply_text(
            f"📊 *{name}*\n\n"
            f"⚠️ No clear signal right now.\n"
            f"Market is neutral — no strong RSI/EMA setup.\n\n"
            f"_Try again in 1-2 minutes or check another pair._",
            parse_mode="Markdown"
        )


def validate_config():
    errors = []
    if not config.TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is not set")
    if not config.TELEGRAM_CHANNEL_ID:
        errors.append("TELEGRAM_CHANNEL_ID is not set")
    if errors:
        print("[ERROR] Missing environment variables:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)


async def on_tick(symbol: str, price: float):
    """Called on every tick — store data AND check for auto signal."""
    signal = engine.add_tick(symbol, price)
    if signal and notifier:
        name = config.SYMBOL_NAMES.get(symbol, symbol)
        print(
            f"[AUTO SIGNAL] {name} | "
            f"{signal.direction} | "
            f"{signal.confidence:.0f}% | "
            f"RSI: {signal.rsi:.1f}"
        )
        await notifier.send_signal(signal)


async def main():
    global notifier, app

    validate_config()

    print("=" * 42)
    print("  Deriv OTC Signal Bot [Auto + Request]")
    print(f"  Monitoring {len(config.OTC_SYMBOLS)} OTC pairs")
    print(f"  Min confidence: {config.MIN_CONFIDENCE}%")
    print("=" * 42)

    notifier = TelegramNotifier()

    # Build Telegram app
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("pairs", cmd_pairs))
    app.add_handler(CommandHandler("signal", cmd_signal))

    await app.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("pairs", "List all OTC pairs"),
        BotCommand("signal", "Request a signal e.g /signal eurusd"),
    ])

    # Start Deriv WebSocket in background
    deriv = DerivClient(on_tick=on_tick)
    asyncio.create_task(deriv.connect())

    # Send startup message
    await notifier.send_startup()

    # Start polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    print("[BOT] Running — Auto signals + Request mode active!")
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[BOT] Stopped.")

# 📊 Deriv OTC Signal Bot

Real-time binary options signal bot using **Deriv API** → **Telegram**.  
Trade signals manually on **Pocket Option**.

---

## 🏗️ Architecture

```
Deriv WebSocket API
      ↓ (real-time OTC tick data)
Signal Engine (RSI + EMA + Bollinger Bands)
      ↓ (signal detected)
Telegram Bot
      ↓ (signal alert)
You → Pocket Option
```

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/deriv-signal-bot.git
cd deriv-signal-bot
```

### 2. Create a Telegram Bot
1. Open Telegram → search `@BotFather`
2. Send `/newbot` and follow the steps
3. Copy the **Bot Token**
4. Add the bot to your channel/group as admin
5. Get your **Channel ID** (use `@userinfobot` or check via API)

### 3. Get a Deriv App ID
1. Go to https://app.deriv.com/account/api-token
2. Or register an app at https://developers.deriv.com/
3. The default App ID `1089` works for testing

### 4. Set environment variables

**Local (.env file):**
```bash
cp .env.example .env
# Edit .env with your values
```

**Railway (production):**
- Go to your Railway project → Variables tab
- Add:
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHANNEL_ID`
  - `DERIV_APP_ID` (optional, default is 1089)

---

## 🚀 Deploy to Railway

1. Push code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo
4. Add environment variables in Railway dashboard
5. Railway auto-detects `Procfile` and runs `python main.py`

---

## 📈 Signal Strategy

Signals are generated using **3 indicators**:

| Indicator | CALL Condition | PUT Condition |
|-----------|---------------|---------------|
| RSI (14) | < 30 (oversold) | > 70 (overbought) |
| EMA (9/21) | Fast crosses above slow | Fast crosses below slow |
| Bollinger Bands | Price hits lower band | Price hits upper band |

**Confidence scoring:**
- RSI extreme: +40 pts
- EMA crossover: +35 pts  
- BB touch: +25 pts
- Min to broadcast: 60 pts

---

## 📱 Signal Format

```
🔥 SIGNAL ALERT 🔥
────────────────────────────
📊 Asset: EUR/USD OTC
🟢 Direction: ⬆️ CALL
⏰ Expiry: 3 min
🎯 Entry Price: 1.08432

📈 RSI: 28.4
💡 Reason: RSI oversold (28.4) + Bullish EMA crossover

🎯 Confidence:
████████░░ 75%
────────────────────────────
🕐 14:32:11 UTC

⚠️ Trade on Pocket Option. Always manage risk.
```

---

## 🎛️ Configuration (config.py)

| Setting | Default | Description |
|---------|---------|-------------|
| `MIN_CONFIDENCE` | 60 | Min score to broadcast signal |
| `SIGNAL_COOLDOWN` | 120s | Delay between signals per pair |
| `DEFAULT_EXPIRY` | 3 min | Suggested trade expiry |
| `RSI_PERIOD` | 14 | RSI lookback period |
| `EMA_FAST` / `EMA_SLOW` | 9 / 21 | EMA periods |

---

## ⚠️ Disclaimer

This bot is for **educational purposes**. Binary options trading carries significant risk.  
Always manage your risk and never trade more than you can afford to lose.

import requests
import pandas as pd
import ta
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8557405091:AAHlCI4JwcDwUQJ-QWqqe0WDmSUdMg1u7kg"

# =========================
# FETCH DATA
# =========================
def get_candles(symbol, interval="1m", limit=150):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    data = requests.get(url).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ])

    df["close"] = df["close"].astype(float)
    return df

# =========================
# SIGNAL ENGINE
# =========================
def analyze(df):
    df['ema9'] = ta.trend.ema_indicator(df['close'], window=9)
    df['ema21'] = ta.trend.ema_indicator(df['close'], window=21)
    df['ema50'] = ta.trend.ema_indicator(df['close'], window=50)
    df['ema200'] = ta.trend.ema_indicator(df['close'], window=200)
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0

    # Trend
    if last['ema50'] > last['ema200']:
        trend = "UP"
        score += 1
    else:
        trend = "DOWN"
        score += 1

    # RSI
    if last['rsi'] < 35:
        score += 1
    if last['rsi'] > 65:
        score += 1

    # EMA crossover
    if prev['ema9'] < prev['ema21'] and last['ema9'] > last['ema21']:
        score += 2
        signal = "BUY"
    elif prev['ema9'] > prev['ema21'] and last['ema9'] < last['ema21']:
        score += 2
        signal = "SELL"
    else:
        signal = "WAIT"

    confidence = min(score * 20, 100)

    return signal, confidence, trend, round(last['rsi'], 2)

# =========================
# MULTI SIGNALS
# =========================
def generate_multiple_signals(df):
    signals = []

    for i in range(5):
        signal, conf, trend, rsi = analyze(df)

        if signal != "WAIT":
            signals.append((signal, conf, trend, rsi))

    return signals

# =========================
# FORMAT OUTPUT
# =========================
def format_signals(pair, signals):
    if not signals:
        return f"❌ No strong signals for {pair}"

    msg = f"📊 {pair} SIGNALS\n\n"

    for i, (sig, conf, trend, rsi) in enumerate(signals):
        msg += f"""
{i+1}. {sig}
Trend: {trend}
RSI: {rsi}
Confidence: {conf}%
"""

    return msg

# =========================
# TELEGRAM COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Send pair like:\nBTC/USDT\nETH/USDT"
    )

# USER REQUEST SIGNAL
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pair = update.message.text.upper().replace("/", "")
    
    try:
        df = get_candles(pair)

        signals = generate_multiple_signals(df)
        msg = format_signals(pair, signals)

        await update.message.reply_text(msg)

    except:
        await update.message.reply_text("❌ Invalid pair")

# =========================
# AUTO SIGNAL SYSTEM
# =========================
async def auto_signals(context: ContextTypes.DEFAULT_TYPE):
    pairs = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

    for pair in pairs:
        try:
            df = get_candles(pair)
            signal, conf, trend, rsi = analyze(df)

            if signal != "WAIT" and conf > 60:
                msg = f"""
🚨 AUTO SIGNAL 🚨

📊 {pair}
Signal: {signal}
Trend: {trend}
RSI: {rsi}
Confidence: {conf}%
"""
                await context.bot.send_message(chat_id=context.job.chat_id, text=msg)

        except:
            pass

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Auto signals every 60 sec
    app.job_queue.run_repeating(auto_signals, interval=60, first=10)

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
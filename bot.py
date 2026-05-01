import requests
import pandas as pd
import ta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8557405091:AAHlCI4JwcDwUQJ-QWqqe0WDmSUdMg1u7kg"

# Convert pair format (USD/JPY → USDJPY)
def format_symbol(pair):
    return pair.replace("/", "").upper()

# Fetch Binance candles
def get_candles(symbol, interval="1m", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    data = requests.get(url).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "close_time","qav","trades","tbbav","tbqav","ignore"
    ])

    df["close"] = df["close"].astype(float)
    return df

# Signal logic (RSI + EMA)
def generate_signal(df):
    df['ema9'] = ta.trend.ema_indicator(df['close'], window=9)
    df['ema21'] = ta.trend.ema_indicator(df['close'], window=21)
    df['ema50'] = ta.trend.ema_indicator(df['close'], window=50)
    df['ema200'] = ta.trend.ema_indicator(df['close'], window=200)
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # BUY
    if (
        last['ema50'] > last['ema200'] and
        last['rsi'] < 35 and
        prev['ema9'] < prev['ema21'] and
        last['ema9'] > last['ema21']
    ):
        return "BUY"

    # SELL
    elif (
        last['ema50'] < last['ema200'] and
        last['rsi'] > 65 and
        prev['ema9'] > prev['ema21'] and
        last['ema9'] < last['ema21']
    ):
        return "SELL"

    return "NO SIGNAL"

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Send currency pair like:\n\nUSD/JPY\nBTC/USDT"
    )

# Handle user input
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pair = update.message.text.strip()
    symbol = format_symbol(pair)

    try:
        df = get_candles(symbol)
        signal = generate_signal(df)

        msg = f"""
📊 Pair: {pair}
⏱ Timeframe: 1 Minute

Signal: {signal}
"""

        await update.message.reply_text(msg)

    except Exception as e:
        await update.message.reply_text("❌ Invalid pair or data not available")

# Auto signals every X minutes
async def auto_signals(context: ContextTypes.DEFAULT_TYPE):
    pairs = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

    for pair in pairs:
        try:
            df = get_candles(pair)
            signal = generate_signal(df)

            if signal != "NO SIGNAL":
                msg = f"""
🚨 AUTO SIGNAL 🚨

📊 Pair: {pair}
⏱ Timeframe: 1m

Signal: {signal}
"""
                await context.bot.send_message(chat_id=context.job.chat_id, text=msg)

        except:
            pass

# Main function
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Auto signals every 60 seconds
    app.job_queue.run_repeating(auto_signals, interval=60, first=10)

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
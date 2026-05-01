import logging
logging.basicConfig(level=logging.INFO)

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest
import random
import os

TOKEN = os.getenv("TOKEN")

def analyze():
    signal = random.choice(["BUY", "SELL"])
    trend = random.choice(["UP", "DOWN"])
    risk = random.choice(["SAFE", "RISKY"])
    return signal, trend, risk

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is working! Use /signal")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s, t, r = analyze()

    msg = f"""
📊 Signal: {s}
📈 Trend: {t}
⚠️ Market: {r}
"""
    await update.message.reply_text(msg)

request = HTTPXRequest(connect_timeout=30, read_timeout=30)

app = ApplicationBuilder().token(TOKEN).request(request).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))

print("Bot running...")
app.run_polling()
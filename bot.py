import logging
logging.basicConfig(level=logging.INFO)

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import random

TOKEN = "YOUR_NEW_TOKEN"

# ✅ FIXED FUNCTION
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

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))

app.run_polling()
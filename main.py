from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import os

TOKEN = os.environ["BOT_TOKEN"]

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👷‍♂️ Bot activo. Escribe 'cotizar' para comenzar."
    )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, responder))
app.run_polling()

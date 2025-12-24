import os
import logging
import threading
from flask import Flask
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- 1. KOYEB HEALTH CHECK SERVER ---
# This keeps the bot from being shut down by Koyeb
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

def run_flask():
    # Koyeb provides a PORT environment variable automatically
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

# --- 2. BOT CONFIGURATION ---
# Use Environment Variables for security (Set these in Koyeb Dashboard)
TOKEN = os.getenv('7953457415:AAE2sw1kMq6IlteojeEjXHCeivqteAOpm2k')
LOG_CHAT_ID = os.getenv('6328052501')
LEADER_HANDLE = '@DLmkt_p1_T162'
MAX_OT_MINUTES = 150

ot_tracker = {}
logging.basicConfig(level=logging.INFO)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    user = update.message.from_user
    user_mention = f"@{user.username}" if user.username else user.first_name
    now = datetime.now()

    # LOGGING (To see deleted messages)
    if LOG_CHAT_ID:
        try:
            log_entry = f"📩 **Log** from {user_mention}:\n{update.message.text}"
            await context.bot.send_message(chat_id=LOG_CHAT_ID, text=log_entry)
        except:
            pass

    # OT REACH
    if text == "ot reach":
        ot_tracker[user.id] = now
        await update.message.reply_text(f"✅ {user_mention}, OT started at {now.strftime('%H:%M:%S')}.")

    # OT OUT
    elif text == "ot out":
        if user.id not in ot_tracker:
            await update.message.reply_text(f"⚠️ {user_mention}, you didn't start OT!")
            return

        start_time = ot_tracker.pop(user.id)
        duration = now - start_time
        duration_minutes = duration.total_seconds() / 60
        h, m = divmod(int(duration_minutes), 60)

        if duration_minutes > MAX_OT_MINUTES:
            await update.message.reply_text(f"🚨 **Attention {LEADER_HANDLE}**\nStaff {user_mention} forgot to OT Out.\nDuration: {h}h {m}m.")
        else:
            await update.message.reply_text(f"🕒 **OT Summary: {user_mention}**\nDuration: {h}h {m}m\nCC: {LEADER_HANDLE}")

def main():
    # Start Flask in a separate thread so it doesn't block the bot
    threading.Thread(target=run_flask, daemon=True).start()

    # Start the Telegram Bot
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()

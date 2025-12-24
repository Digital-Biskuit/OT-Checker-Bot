import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = '7953457415:AAE2sw1kMq6IlteojeEjXHCeivqteAOpm2k'
LEADER_HANDLE = '@DLmkt_p1_T162'
# Create a private group and get its ID to send deleted/all logs there
# Or just use your own User ID to get logs in DM
LOG_CHAT_ID = '6328052501' 
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

    # --- 1. LOGGING TRIGGER ---
    # This sends a copy of EVERY message to your log chat.
    # Even if they delete it in the main group, the copy remains in your Log Chat.
    log_entry = f"📩 **Message Log**\nFrom: {user_mention}\nText: {update.message.text}"
    await context.bot.send_message(chat_id=LOG_CHAT_ID, text=log_entry)

    # --- 2. OT LOGIC ---
    if text == "ot reach":
        ot_tracker[user.id] = now
        await update.message.reply_text(f"✅ {user_mention}, OT started at {now.strftime('%H:%M:%S')}.")

    elif text == "ot out":
        if user.id not in ot_tracker:
            await update.message.reply_text(f"⚠️ {user_mention}, you didn't start OT!")
            return

        start_time = ot_tracker.pop(user.id)
        duration = now - start_time
        duration_minutes = duration.total_seconds() / 60
        
        h, m = divmod(int(duration_minutes), 60)

        if duration_minutes > MAX_OT_MINUTES:
            await update.message.reply_text(
                f"🚨 **Attention {LEADER_HANDLE}**\n"
                f"Staff {user_mention} forgot to OT Out.\n

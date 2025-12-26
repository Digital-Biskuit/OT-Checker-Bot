import logging
import pytz
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "7953457415:AAE2sw1kMq6IlteojeEjXHCeivqteAOpm2k"
MAX_OT_MINUTES = 150 
LOCAL_TZ = pytz.timezone('Asia/Yangon') 

# Memory for tracking
message_cache = {}
ot_tracking = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_now():
    return datetime.now(LOCAL_TZ)

async def monitor_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. DETECT DELETIONS
    if update.deleted_message:
        msg_id = update.deleted_message.message_id
        if msg_id in message_cache:
            data = message_cache[msg_id]
            alert = (f"🗑️ **Deleted Message Detected**\n"
                     f"👤 **From:** {data['user']}\n"
                     f"📝 **Content:** {data['text']}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=alert, parse_mode="Markdown")
            return

    # 2. CACHE NEW MESSAGES & OT LOGIC
    if update.message and update.message.text:
        user = update.message.from_user
        text = update.message.text
        msg_id = update.message.message_id
        now = get_now()

        # Save to cache
        message_cache[msg_id] = {"text": text, "user": user.first_name}

        # OT Logic
        lower_text = text.lower()
        if lower_text == "ot reach":
            ot_tracking[user.id] = now
            await update.message.reply_text(f"✅ OT Started for {user.first_name} at {now.strftime('%I:%M %p')}.")
        
        elif lower_text == "ot out":
            if user.id in ot_tracking:
                start_time = ot_tracking.pop(user.id)
                duration = now - start_time
                mins = int(duration.total_seconds() / 60)
                msg = f"🕒 OT Complete for {user.first_name}\nDuration: {mins//60}h {mins%60}m"
                if mins > MAX_OT_MINUTES:
                    msg = f"⚠️ {user.first_name} exceeded max OT limit!\nDuration: {mins//60}h {mins%60}m"
                await update.message.reply_text(msg)

def main():
    app = Application.builder().token(TOKEN).build()

    # Filters.ALL ensures we catch deletions AND text
    app.add_handler(MessageHandler(filters.ALL, monitor_handler))

    print(f"Bot Active. Timezone: Asia/Yangon. Current Time: {get_now().strftime('%I:%M %p')}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

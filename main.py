import logging
import pytz
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "7953457415:AAE2sw1kMq6IlteojeEjXHCeivqteAOpm2k"
MAX_OT_MINUTES = 150 
LOCAL_TZ = pytz.timezone('Asia/Yangon') 

# Memory
message_cache = {}
ot_tracking = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_now():
    return datetime.now(LOCAL_TZ)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    user = update.message.from_user
    text = update.message.text
    msg_id = update.message.message_id
    now = get_now()

    # 1. CACHE MESSAGE
    message_cache[msg_id] = {
        "text": text,
        "user": user.first_name
    }

    # 2. OT LOGIC
    lower_text = text.lower()
    if lower_text == "ot reach":
        ot_tracking[user.id] = now
        await update.message.reply_text(f"✅ OT Started for {user.first_name} at {now.strftime('%I:%M %p')}.")

    elif lower_text == "ot out":
        if user.id in ot_tracking:
            start_time = ot_tracking.pop(user.id)
            duration = now - start_time
            mins = int(duration.total_seconds() / 60)
            
            hours = mins // 60
            remaining_mins = mins % 60

            if mins > MAX_OT_MINUTES:
                msg = (f"⚠️ {user.first_name} forgot to OT out!\n"
                       f"Max time exceeded. Duration recorded: {hours}h {remaining_mins}m")
            else:
                msg = (f"🕒 OT Complete for {user.first_name}\n"
                       f"Duration: {hours}h {remaining_mins}m")
            
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❌ You haven't started an OT session yet.")

# --- DELETE MONITOR ---
async def track_deleted_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.deleted_message:
        msg_id = update.deleted_message.message_id
        if msg_id in message_cache:
            data = message_cache[msg_id]
            alert = (
                f"🗑️ **Deleted Message**\n"
                f"👤 **From:** {data['user']}\n"
                f"📝 **Content:** {data['text']}"
            )
            await context.bot.send_message(chat_id=update.effective_chat.id, text=alert, parse_mode="Markdown")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType.DELETED_MESSAGE, track_deleted_messages))

    print("Bot started without leader notifications.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

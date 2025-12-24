import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "7953457415:AAE2sw1kMq6IlteojeEjXHCeivqteAOpm2k"
LEADER_USERNAME = "@DLmkt_p1_T162"
MAX_OT_MINUTES = 150 

# Dictionaries for tracking
ot_tracking = {}
message_cache = {} # Stores {message_id: {"text": text, "user": name}}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    user = update.message.from_user
    text = update.message.text
    msg_id = update.message.message_id
    now = datetime.now()

    # --- SAVE TO CACHE ---
    # We must store the text NOW, because once it's deleted, we can't get it back
    message_cache[msg_id] = {
        "text": text,
        "user": user.first_name
    }

    # --- OT LOGIC ---
    lower_text = text.lower()
    if lower_text == "ot reach":
        ot_tracking[user.id] = now
        await update.message.reply_text(f"✅ OT Started for {user.first_name} at {now.strftime('%H:%M:%S')}.")

    elif lower_text == "ot out":
        if user.id in ot_tracking:
            start_time = ot_tracking.pop(user.id)
            duration = now - start_time
            duration_minutes = duration.total_seconds() / 60
            
            hours = int(duration_minutes // 60)
            minutes = int(duration_minutes % 60)

            if duration_minutes > MAX_OT_MINUTES:
                msg = (f"⚠️ {user.first_name} clocked out, but exceeded max duration!\n"
                       f"Duration: {hours}h {minutes}m\n"
                       f"Cc Leader: {LEADER_USERNAME}")
            else:
                msg = (f"🕒 OT Complete for {user.first_name}\n"
                       f"Duration: {hours}h {minutes}m\n"
                       f"Notifying Leader: {LEADER_USERNAME}")
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❌ You haven't started an OT session yet. Type 'OT Reach'.")

# --- IMPROVED DELETE TRACKER ---
async def track_deleted_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This specifically checks for the 'deleted_message' attribute in the update
    if update.deleted_message:
        msg_id = update.deleted_message.message_id
        if msg_id in message_cache:
            data = message_cache[msg_id]
            log_text = (f"🗑️ **Deleted Message Detected**\n"
                        f"👤 **From:** {data['user']}\n"
                        f"📝 **Content:** {data['text']}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=log_text, parse_mode="Markdown")
            del message_cache[msg_id]

def main():
    app = Application.builder().token(TOKEN).build()

    # Main handler for text and caching
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Correct handler for deleted messages
    app.add_handler(MessageHandler(filters.UpdateType.DELETED_MESSAGE, track_deleted_messages))

    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES) # Important: tell Telegram to send all updates

if __name__ == '__main__':
    main()

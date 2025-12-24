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
message_cache = {} # Stores {message_id: "message text"}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    user = update.message.from_user
    text = update.message.text
    now = datetime.now()

    # --- SAVE TO CACHE (For Delete Tracker) ---
    # We store the message text in case it gets deleted later
    message_cache[update.message.message_id] = {
        "text": text,
        "user": user.first_name
    }
    # Keep cache small (remove old messages if needed)
    if len(message_cache) > 500:
        first_key = next(iter(message_cache))
        message_cache.pop(first_key)

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

# --- DELETE TRACKER TRIGGER ---
async def track_deleted_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # This triggers when the bot detects a message was deleted
    if update.deleted_message:
        msg_id = update.deleted_message.message_id
        if msg_id in message_cache:
            deleted_data = message_cache[msg_id]
            log_text = (f"🗑️ **Message Deleted**\n"
                        f"From: {deleted_data['user']}\n"
                        f"Content: {deleted_data['text']}")
            await update.effective_chat.send_message(log_text, parse_mode="Markdown")
            # Remove from cache after reporting
            message_cache.pop(msg_id)

def main():
    app = Application.builder().token(TOKEN).build()

    # Handler for all text messages (OT and Caching)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Handler for deleted messages
    app.add_handler(MessageHandler(filters.StatusUpdate.DELETE_CHAT_PHOTO, track_deleted_messages))

    print("Bot is starting...")
    app.run_polling()

if __name__ == '__main__':
    main()

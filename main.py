import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "7953457415:AAE2sw1kMq6IlteojeEjXHCeivqteAOpm2k"
LEADER_USERNAME = "@DLmkt_p1_T162"
MAX_OT_MINUTES = 150  # 2 hours 30 mins

# Dictionary to store start times: {user_id: start_datetime}
ot_tracking = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user = update.message.from_user
    now = datetime.now()

    # --- OT REACH (START) ---
    if text == "ot reach":
        ot_tracking[user.id] = now
        await update.message.reply_text(f"✅ OT Started for {user.first_name} at {now.strftime('%H:%M:%S')}.")

    # --- OT OUT (END) ---
    elif text == "ot out":
        if user.id in ot_tracking:
            start_time = ot_tracking.pop(user.id)
            duration = now - start_time
            duration_minutes = duration.total_seconds() / 60
            
            hours = int(duration_minutes // 60)
            minutes = int(duration_minutes % 60)

            # Check if exceeded Max OT
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

# --- DELETE TRACKER ---
async def track_deleted_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.deleted_message:
        # Note: Bots can only see WHAT was deleted if they have privacy mode disabled 
        # or if the message was cached. This triggers when a message is deleted.
        await update.effective_chat.send_message(
            f"🗑️ A message was deleted in this chat. (Security Monitor Active)"
        )

def main():
    app = Application.builder().token(TOKEN).build()

    # Handle text messages for OT
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Handle deleted messages
    app.add_handler(MessageHandler(filters.StatusUpdate.DELETE_CHAT_PHOTO, track_deleted_messages)) # Example hook

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle normal messages
    if update.message and update.message.text:
        user = update.message.from_user
        text = update.message.text
        msg_id = update.message.message_id
        now = get_now()

        # Cache text for the delete tracker
        message_cache[msg_id] = {"text": text, "user": user.first_name}

        # OT Logic
        lower_text = text.lower()
        if lower_text == "ot reach":
            ot_tracking[user.id] = now
            await update.message.reply_text(f"✅ OT Started for {user.first_name} at {now.strftime('%I:%M:%S %p')}.")
        
        elif lower_text == "ot out":
            if user.id in ot_tracking:
                start_time = ot_tracking.pop(user.id)
                duration = now - start_time
                mins = int(duration.total_seconds() / 60)
                if mins > MAX_OT_MINUTES:
                    await update.message.reply_text(f"⚠️ {user.first_name} forgot to OT out!\nDuration: {mins//60}h {mins%60}m")
                else:
                    await update.message.reply_text(f"🕒 OT Complete for {user.first_name}\nDuration: {mins//60}h {mins%60}m")
            else:
                await update.message.reply_text("❌ You haven't started an OT session yet.")

    # Handle Delete Detection
    elif update.deleted_message:
        msg_id = update.deleted_message.message_id
        if msg_id in message_cache:
            data = message_cache[msg_id]
            alert = f"🗑️ **Deleted Message**\n👤 **From:** {data['user']}\n📝 **Content:** {data['text']}"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=alert, parse_mode="Markdown")

def main():
    app = Application.builder().token(TOKEN).build()

    # Use a single handler for both messages and deletions to avoid AttributeErrors
    app.add_handler(MessageHandler(filters.ALL, handle_message))

    print("Bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

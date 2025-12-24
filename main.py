import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "7953457415:AAE2sw1kMq6IlteojeEjXHCeivqteAOpm2k"
LEADER_USERNAME = "@DLmkt_p1_T162"
MAX_OT_MINUTES = 150 

ot_tracking = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    text = update.message.text.lower()
    user = update.message.from_user
    now = datetime.now()

    if text == "ot reach":
        ot_tracking[user.id] = now
        await update.message.reply_text(f"✅ OT Started for {user.first_name} at {now.strftime('%H:%M:%S')}.")

    elif text == "ot out":
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

def main():
    # Application builder handles the connection
    app = Application.builder().token(TOKEN).build()

    # Handle text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is starting...")
    app.run_polling()

if __name__ == '__main__':
    main()

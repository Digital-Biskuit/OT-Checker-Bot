import logging
import pytz
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "7953457415:AAE2sw1kMq6IlteojeEjXHCeivqteAOpm2k"
MAX_OT_MINUTES = 150 
LOCAL_TZ = pytz.timezone('Asia/Yangon') 

# Dictionary to store start times: {user_id: start_datetime}
ot_tracking = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_now():
    return datetime.now(LOCAL_TZ)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    user = update.message.from_user
    text = update.message.text
    now = get_now()

    # --- OT LOGIC ---
    lower_text = text.lower()
    
    # Trigger for "OT Reach"
    if lower_text == "ot reach":
        ot_tracking[user.id] = now
        await update.message.reply_text(f"✅ OT Started for {user.first_name} at {now.strftime('%I:%M %p')}.")

    # Trigger for "OT Out"
    elif lower_text == "ot out":
        if user.id in ot_tracking:
            start_time = ot_tracking.pop(user.id)
            duration = now - start_time
            mins = int(duration.total_seconds() / 60)
            
            hours = mins // 60
            remaining_mins = mins % 60

            if mins > MAX_OT_MINUTES:
                # If staff forget to OT out (exceeds 2h 30m)
                msg = (f"⚠️ {user.first_name} forgot to OT out!\n"
                       f"Max time exceeded. Duration recorded: {hours}h {remaining_mins}m")
            else:
                msg = (f"🕒 OT Complete for {user.first_name}\n"
                       f"Duration: {hours}h {remaining_mins}m")
            
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❌ You haven't started an OT session yet. Type 'OT Reach'.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Handle text messages for OT only
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"Bot started. Current Local Time: {get_now().strftime('%I:%M %p')}")
    app.run_polling()

if __name__ == '__main__':
    main()

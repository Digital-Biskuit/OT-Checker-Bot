import logging
import pytz
import re
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "7953457415:AAE2sw1kMq6IlteojeEjXHCeivqteAOpm2k"
LOCAL_TZ = pytz.timezone('Asia/Yangon')

# --- 3 GROUP SETUP ---
GROUPS = [-1003368401204, -5071975890, -3435024283]

LEADERS = {
    # Added the 3rd ID here so YOU can manage all of them
    6328052501: [-1003368401204, -5071975890, -3435024283], 
    
    # The other leader still has access to their specific group
    7310631701: [-3435024283] 
}

# Nested Storage
ot_tracking = {}
ot_targets = {}
user_codes = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_now():
    return datetime.now(LOCAL_TZ)

def extract_staff_code(text):
    match = re.search(r'[Tt]\d{3,4}', text)
    return match.group(0).upper() if match else None

# --- LEADER COMMAND ---
async def set_ot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = update.message.message_thread_id

    # FIX: Check if the chat_id is INSIDE the list of IDs for that leader
    if user_id not in LEADERS or chat_id not in LEADERS[user_id]:
        await update.message.reply_text("⛔ Access Denied: You are not the leader.")
        return

    try:
        target_username = context.args[0].replace('@', '').lower()
        
        # FIX: Clean the input so "/set_ot @name 60mins" works by removing letters
        mins_input = re.sub(r'\D', '', context.args[1])
        target_mins = int(mins_input)

        key = (chat_id, thread_id)
        if key not in ot_targets: ot_targets[key] = {}
        ot_targets[key][target_username] = target_mins
        
        await update.message.reply_text(f"🎯 Target for @{target_username} set to {target_mins}m in this group.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Usage: `/set_ot @username 60`")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    thread_id = update.message.message_thread_id 
    
    if chat_id not in GROUPS: return

    user = update.message.from_user
    username = user.username.lower() if user.username else str(user.id)
    text = update.message.text
    now = get_now()
    key = (chat_id, thread_id)

    found_code = extract_staff_code(text)
    if found_code:
        user_codes[user.id] = found_code

    lower_text = text.lower()
    
    if lower_text == "ot reach":
        if key not in ot_tracking: ot_tracking[key] = {}
        ot_tracking[key][user.id] = now
        
        target = ot_targets.get(key, {}).get(username, "Not Set")
        display_name = user_codes.get(user.id, user.first_name)
        
        await update.message.reply_text(f"✅ OT Started for {display_name}\n🎯 Target: {target} mins")

    elif lower_text == "ot out":
        if key in ot_tracking and user.id in ot_tracking[key]:
            start_time = ot_tracking[key].pop(user.id)
            duration = now - start_time
            mins = int(duration.total_seconds() / 60)
            
            target_mins = ot_targets.get(key, {}).get(username, 0)
            display_name = user_codes.get(user.id, user.first_name)
            
            status = "✅ COMPLETED" if mins >= target_mins else "❌ INCOMPLETE"
            
            msg = (f"🕒 **OT Summary: {display_name}**\n"
                   f"Result: {status}\n"
                   f"Actual: {mins//60}h {mins%60}m\n"
                   f"Required: {target_mins} mins")
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ No session found. Type 'OT Reach'.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("set_ot", set_ot))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot started. Group and Topic tracking active.")
    app.run_polling()

if __name__ == '__main__':
    main()

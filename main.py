import logging
import pytz
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "7953457415:AAE2sw1kMq6IlteojeEjXHCeivqteAOpm2k"
LOCAL_TZ = pytz.timezone('Asia/Yangon')

# Define your 3 Group IDs and 3 Leader IDs here
GROUPS = {
    -1003368401204: "Group A",
    -1002222222222: "Group B",
    -1003333333333: "Group C"
}

LEADERS = {
    6328052501: -1003368401204,  # Leader 1 ID -> Group A
    # Add Leader 2 and 3 here...
}

# Tracking: { chat_id: { user_id: start_time } }
ot_tracking = {gid: {} for gid in GROUPS}
# Targets: { chat_id: { username_lowercase: target_minutes } }
ot_targets = {gid: {} for gid in GROUPS}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_now():
    return datetime.now(LOCAL_TZ)

# --- LEADER COMMAND: /set_ot @username minutes ---
async def set_ot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id not in LEADERS or LEADERS[user_id] != chat_id:
        await update.message.reply_text("⛔ Access Denied: Only the Leader of this group can set targets.")
        return

    try:
        # Expecting: /set_ot @username 90
        target_username = context.args[0].replace('@', '').lower()
        target_mins = int(context.args[1])

        ot_targets[chat_id][target_username] = target_mins
        await update.message.reply_text(f"🎯 Target for @{target_username} set to {target_mins} minutes.")
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Usage: `/set_ot @username 60` (for 1 hour)")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    chat_id = update.effective_chat.id
    if chat_id not in GROUPS:
        return

    user = update.message.from_user
    username = user.username.lower() if user.username else "no_username"
    text = update.message.text.lower()
    now = get_now()

    # --- OT START ---
    if text == "ot reach":
        ot_tracking[chat_id][user.id] = now
        # Check if this specific username has a target set
        target = ot_targets[chat_id].get(username, "Not Set")
        await update.message.reply_text(
            f"✅ OT Started for @{username}\n"
            f"🎯 Your Target today: {target} mins"
        )

    # --- OT FINISH ---
    elif text == "ot out":
        if user.id in ot_tracking[chat_id]:
            start_time = ot_tracking[chat_id].pop(user.id)
            duration = now - start_time
            actual_mins = int(duration.total_seconds() / 60)
            
            # Get target for this username
            target_mins = ot_targets[chat_id].get(username, 0)
            
            hours = actual_mins // 60
            remaining_mins = actual_mins % 60
            
            status = "✅ COMPLETED" if actual_mins >= target_mins else "❌ INCOMPLETE"
            
            msg = (f"🕒 **OT Summary: @{username}**\n"
                   f"Result: {status}\n"
                   f"Actual: {hours}h {remaining_mins}m\n"
                   f"Required: {target_mins} mins")
            
            await update.message.reply_text(msg, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ No session found. Type 'OT Reach'.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("set_ot", set_ot))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running with Username Targets...")
    app.run_polling()

if __name__ == '__main__':
    main()

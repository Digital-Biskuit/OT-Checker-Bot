import logging
import pytz
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, RawUpdateHandler

# --- CONFIGURATION ---
TOKEN = "7953457415:AAE2sw1kMq6IlteojeEjXHCeivqteAOpm2k"
MAX_OT_MINUTES = 150 
LOCAL_TZ = pytz.timezone('Asia/Yangon') 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS messages (msg_id INTEGER PRIMARY KEY, user_name TEXT, content TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS ot (user_id INTEGER PRIMARY KEY, start_time TEXT)')
    conn.commit()
    conn.close()

def save_message(msg_id, user_name, content):
    with sqlite3.connect('bot_data.db') as conn:
        conn.execute("INSERT OR REPLACE INTO messages VALUES (?, ?, ?)", (msg_id, user_name, content))

def get_now():
    return datetime.now(LOCAL_TZ)

# --- OT LOGIC HANDLER ---
async def handle_ot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    user = update.message.from_user
    text = update.message.text
    msg_id = update.message.message_id
    now = get_now()

    # Save every message for delete detection later
    save_message(msg_id, user.first_name, text)

    lower_text = text.lower()
    if lower_text == "ot reach":
        with sqlite3.connect('bot_data.db') as conn:
            conn.execute("INSERT OR REPLACE INTO ot VALUES (?, ?)", (user.id, now.isoformat()))
        await update.message.reply_text(f"✅ OT Started for {user.first_name} at {now.strftime('%I:%M %p')}.")
    
    elif lower_text == "ot out":
        with sqlite3.connect('bot_data.db') as conn:
            row = conn.execute("SELECT start_time FROM ot WHERE user_id=?", (user.id,)).fetchone()
            if row:
                start_time = datetime.fromisoformat(row[0])
                duration = now - start_time
                mins = int(duration.total_seconds() / 60)
                conn.execute("DELETE FROM ot WHERE user_id=?", (user.id,))
                
                msg = f"🕒 OT Complete for {user.first_name}\nDuration: {mins//60}h {mins%60}m"
                if mins > MAX_OT_MINUTES:
                    msg = f"⚠️ {user.first_name} exceeded max OT limit!\nDuration: {mins//60}h {mins%60}m"
                await update.message.reply_text(msg)
            else:
                await update.message.reply_text("❌ You haven't started an OT session yet.")

# --- THE FIX FOR DELETE DETECTION ---
async def raw_update_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    # This catches the low-level Telegram signal for deletions
    update_dict = update if isinstance(update, dict) else update.to_dict()
    
    # Look for 'updateDeleteMessages' or 'delete_messages' in the raw update
    if "message_ids" in str(update_dict) or update_dict.get("_") == "updateDeleteMessages":
        msg_ids = update_dict.get("messages", []) or update_dict.get("message_ids", [])
        
        for mid in msg_ids:
            with sqlite3.connect('bot_data.db') as conn:
                data = conn.execute("SELECT user_name, content FROM messages WHERE msg_id=?", (mid,)).fetchone()
                if data:
                    alert = f"🗑️ **Deleted Message Detected**\n👤 **From:** {data[0]}\n📝 **Content:** {data[1]}"
                    await context.bot.send_message(chat_id=context._chat_id, text=alert, parse_mode="Markdown")

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    # Standard handler for text/OT
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ot))
    
    # Raw handler for deletions
    app.add_handler(RawUpdateHandler(raw_update_handler))

    print("Bot Active. Monitoring for OT and Deletions...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

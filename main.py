import logging
import pytz
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "7953457415:AAE2sw1kMq6IlteojeEjXHCeivqteAOpm2k"
MAX_OT_MINUTES = 150 
LOCAL_TZ = pytz.timezone('Asia/Yangon') 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    # Table for messages (Delete Detection)
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (msg_id INTEGER PRIMARY KEY, user_name TEXT, content TEXT)''')
    # Table for OT tracking
    c.execute('''CREATE TABLE IF NOT EXISTS ot 
                 (user_id INTEGER PRIMARY KEY, start_time TEXT)''')
    conn.commit()
    conn.close()

def save_message(msg_id, user_name, content):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO messages VALUES (?, ?, ?)", (msg_id, user_name, content))
    conn.commit()
    conn.close()

def get_deleted_msg(msg_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT user_name, content FROM messages WHERE msg_id=?", (msg_id,))
    res = c.fetchone()
    conn.close()
    return res

def get_now():
    return datetime.now(LOCAL_TZ)

async def monitor_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. DETECT DELETIONS
    if update.deleted_message:
        msg_id = update.deleted_message.message_id
        data = get_deleted_msg(msg_id)
        if data:
            alert = (f"🗑️ **Deleted Message Detected**\n"
                     f"👤 **From:** {data[0]}\n"
                     f"📝 **Content:** {data[1]}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text=alert, parse_mode="Markdown")
        return

    # 2. CACHE MESSAGES & OT LOGIC
    if update.message and update.message.text:
        user = update.message.from_user
        text = update.message.text
        msg_id = update.message.message_id
        now = get_now()

        # Save message to permanent database
        save_message(msg_id, user.first_name, text)

        lower_text = text.lower()
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()

        if lower_text == "ot reach":
            start_str = now.isoformat()
            c.execute("INSERT OR REPLACE INTO ot VALUES (?, ?)", (user.id, start_str))
            conn.commit()
            await update.message.reply_text(f"✅ OT Started for {user.first_name} at {now.strftime('%I:%M %p')}.")
        
        elif lower_text == "ot out":
            c.execute("SELECT start_time FROM ot WHERE user_id=?", (user.id,))
            row = c.fetchone()
            if row:
                start_time = datetime.fromisoformat(row[0])
                duration = now - start_time
                mins = int(duration.total_seconds() / 60)
                
                c.execute("DELETE FROM ot WHERE user_id=?", (user.id,))
                conn.commit()

                msg = f"🕒 OT Complete for {user.first_name}\nDuration: {mins//60}h {mins%60}m"
                if mins > MAX_OT_MINUTES:
                    msg = f"⚠️ {user.first_name} exceeded max OT limit!\nDuration: {mins//60}h {mins%60}m"
                await update.message.reply_text(msg)
            else:
                await update.message.reply_text("❌ You haven't started an OT session yet.")
        conn.close()

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, monitor_handler))
    print(f"Bot Active with Database. Time: {get_now().strftime('%I:%M %p')}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

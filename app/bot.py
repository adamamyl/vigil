import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from loguru import logger
from app.database import add_to_queue

# Optional: Add your Telegram User ID here to restrict access
# You can find your ID by messaging @userinfobot
ALLOWED_USER_IDS = [] 

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Validates the user and the URL, then pushes to the SQLite queue.
    """
    if not update.message or not update.message.text:
        return

    user_id = update.message.from_user.id
    
    # Simple security gate
    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        logger.warning(f"🚫 Unauthorized access attempt by ID: {user_id}")
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return

    url = update.message.text.strip()
    
    if url.startswith(("http://", "https://")):
        try:
            add_to_queue(url)
            logger.info(f"📩 Queued: {url}")
            await update.message.reply_text("✅ Added to the 4 AM sweep.")
        except Exception as e:
            logger.error(f"❌ DB Error: {e}")
            await update.message.reply_text("⚠️ Failed to queue link.")
    else:
        await update.message.reply_text("🤔 Send me a valid URL (YouTube, Reddit, etc.)")

def run_bot():
    """Starts the Telegram polling loop."""
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.critical("🚫 TELEGRAM_TOKEN not set!")
        return

    application = ApplicationBuilder().token(token).build()
    
    msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(msg_handler)
    
    logger.info("🤖 Vigil Bot is now on watch (polling)...")
    
    # CRITICAL FIX: stop_signals=False allows it to run in a background thread
    application.run_polling(stop_signals=False)
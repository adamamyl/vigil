import threading
import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

# Load .env file before importing our internal modules
# This allows us to use variables like DATA_DIR immediately
load_dotenv() 

from app.bot import run_bot
from app.processor import run_sweep
from app.database import init_db, get_pending, add_to_queue, Session, DownloadQueue

app = Flask(__name__)

# Configure Logging with Month Rotation
# We use a default if DATA_DIR isn't set yet
DATA_DIR = os.getenv("DATA_DIR", "./data")
# Ensure the base DATA_DIR and logs subdir exist
os.makedirs(DATA_DIR, exist_ok=True)
LOG_FILE = os.path.join(DATA_DIR, "logs/vibe.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logger.add(
    LOG_FILE, 
    rotation="1 month", 
    retention=1, 
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

@app.route("/")
def index():
    """Render the dashboard with current queue status."""
    return render_template("index.html", queue=get_pending())

@app.route("/add-url", methods=["POST"])
def web_add_url():
    """Manual URL addition via the Web UI form."""
    url = request.form.get("url")
    if url:
        url = url.strip()
        if url.startswith(("http://", "https://")):
            try:
                # Reuse the same DB logic as the Telegram bot for idempotency
                add_to_queue(url)
                logger.info(f"🔗 URL added via Web UI: {url}")
            except Exception as e:
                logger.error(f"❌ Failed to add URL via Web: {e}")
    
    return redirect(url_for("index"))

@app.route("/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    """Delete a specific item from the queue if it hasn't been downloaded yet."""
    try:
        with Session() as session:
            item = session.query(DownloadQueue).filter_by(id=item_id).first()
            
            # Safety Check: Only delete if not completed or currently downloading
            if item and item.status not in ['completed', 'downloading']:
                logger.info(f"🗑️ Vigil removed pending item: {item.url}")
                session.delete(item)
                session.commit()
            else:
                logger.warning(f"⚠️ Refused to delete item {item_id}: Status is {item.status}")
                
    except Exception as e:
        logger.error(f"❌ Failed to delete item {item_id}: {e}")
    
    return redirect(url_for("index"))

@app.route("/run-now", methods=["POST"])
def run_now():
    """Manual trigger for the downloader sweep."""
    logger.info("Manual sweep triggered via Web UI")
    # Run in a thread so the UI doesn't hang while yt-dlp works
    threading.Thread(target=run_sweep, daemon=True).start()
    return redirect(url_for("index"))

if __name__ == "__main__":
    # Ensure database is created and ready
    init_db()
    
    # Scheduler setup
    scheduler = BackgroundScheduler()
    sweep_hour = int(os.getenv("SWEEP_HOUR", 4))
    scheduler.add_job(run_sweep, 'cron', hour=sweep_hour, minute=0)
    scheduler.start()
    logger.info(f"⏰ Vigil scheduler active: Sweep set for {sweep_hour}:00 daily.")
    
    # Run Telegram Bot in a background thread
    # stop_signals=False is required when running bot in a secondary thread
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Run Flask UI
    # Using 5005 to avoid common macOS AirPlay port conflicts on 5000
    port = int(os.getenv("PORT", 5005))
    logger.info(f"🌐 Vigil Web UI starting on [http://0.0.0.0](http://0.0.0.0):{port}")
    app.run(host="0.0.0.0", port=port)
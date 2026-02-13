import threading
import os
from dotenv import load_dotenv  # <-- Add this
from flask import Flask, render_template, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

# Load .env file before importing our internal modules
load_dotenv() 

from app.bot import run_bot
from app.processor import run_sweep
from app.database import init_db, get_pending

app = Flask(__name__)

# Configure Logging with Month Rotation
# We use a default if DATA_DIR isn't set yet
DATA_DIR = os.getenv("DATA_DIR", "./data")
LOG_FILE = os.path.join(DATA_DIR, "logs/vibe.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logger.add(LOG_FILE, rotation="1 month", retention=1, compression="zip")

@app.route("/")
def index():
    return render_template("index.html", queue=get_pending())

@app.route("/run-now", methods=["POST"])
def run_now():
    logger.info("Manual sweep triggered via Web UI")
    threading.Thread(target=run_sweep, daemon=True).start()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    
    # Scheduler setup
    scheduler = BackgroundScheduler()
    sweep_hour = int(os.getenv("SWEEP_HOUR", 4))
    scheduler.add_job(run_sweep, 'cron', hour=sweep_hour, minute=0)
    scheduler.start()
    logger.info(f"⏰ Vigil scheduler active: Sweep set for {sweep_hour}:00 daily.")
    
    # Run Telegram Bot in a background thread
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Run Flask UI
    # Note: On macOS, port 5000 is often taken by AirPlay. 
    # Using 5005 to avoid the conflict.
    port = int(os.getenv("PORT", 5005))
    logger.info(f"🌐 Vigil Web UI starting on [http://0.0.0.0](http://0.0.0.0):{port}")
    app.run(host="0.0.0.0", port=port)
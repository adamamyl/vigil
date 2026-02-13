# 🎥 Vibe Downloader
Minimalist, idempotent video downloader for Synology NAS via Telegram.

## Setup
1. Create a `.env` file from the template.
2. Ensure your NAS path is correctly mounted in `docker-compose.yml`.
3. Run `docker compose up -d`.

## Automation
- **Telegram**: URLs are queued as soon as you share them with the bot.
- **Sweep**: Every night at 4 AM (configurable via `SWEEP_HOUR`).
"""
Entry point for the coaching Telegram bot.

Usage:
    python bot.py
"""

import logging
import os

from dotenv import load_dotenv
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from database import init_db
from handlers import (
    cmd_checkin,
    cmd_start,
    cmd_stats,
    cmd_today,
    cmd_week,
    handle_callback,
    handle_text,
)
from scheduler import setup_jobs

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
load_dotenv()
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]


def main() -> None:
    init_db()
    log.info("Database initialised.")

    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("checkin", cmd_checkin))
    app.add_handler(CommandHandler("today",   cmd_today))
    app.add_handler(CommandHandler("stats",   cmd_stats))
    app.add_handler(CommandHandler("week",    cmd_week))

    # Inline keyboard callbacks (check-in quick values)
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Free text input during check-in
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Scheduled jobs
    setup_jobs(app)

    log.info("Bot started. Listening for updates...")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
    )


if __name__ == "__main__":
    main()

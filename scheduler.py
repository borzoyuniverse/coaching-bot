"""
Scheduled jobs using PTB's built-in JobQueue (backed by APScheduler).

Jobs are registered in bot.py after the Application is built.
"""

import logging
from datetime import time

import pytz

from database import get_setting
from messages import morning_message
from handlers import start_checkin_flow

log = logging.getLogger(__name__)

TZ = pytz.timezone("Asia/Omsk")  # UTC+6

MORNING_TIME = time(8, 0, 0, tzinfo=TZ)
EVENING_TIME = time(20, 0, 0, tzinfo=TZ)


async def job_morning(context) -> None:
    """Send morning planning summary."""
    chat_id = get_setting("chat_id")
    if not chat_id:
        log.warning("job_morning: chat_id not set yet (user hasn't done /start)")
        return
    text = morning_message()
    await context.bot.send_message(chat_id=int(chat_id), text=text, parse_mode="HTML")


async def job_evening(context) -> None:
    """Start evening check-in flow."""
    chat_id = get_setting("chat_id")
    if not chat_id:
        log.warning("job_evening: chat_id not set yet (user hasn't done /start)")
        return
    await start_checkin_flow(context.bot, int(chat_id))


def setup_jobs(app) -> None:
    """Register all scheduled jobs on the application's job queue."""
    jq = app.job_queue
    jq.run_daily(job_morning, time=MORNING_TIME, name="morning")
    jq.run_daily(job_evening, time=EVENING_TIME, name="evening")
    log.info("Scheduled: morning %s, evening %s (UTC+6)", MORNING_TIME, EVENING_TIME)

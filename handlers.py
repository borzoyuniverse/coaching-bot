"""
Command handlers and evening check-in conversation flow.

Check-in state is persisted to SQLite so bot restarts don't break an
ongoing check-in session.
"""

import logging
from datetime import date

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import (
    checkin_advance,
    checkin_end,
    checkin_get,
    checkin_start,
    get_setting,
    save_setting,
    upsert_metric,
)
from messages import daily_summary, morning_message, weekly_summary
from plan import METRICS, get_week_number

log = logging.getLogger(__name__)

QUICK_VALUES = [0, 1, 2, 3, 5, 10]


# ── Keyboard ───────────────────────────────────────────────────────────────────

def _metric_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(str(v), callback_data=f"ci_{v}")
        for v in QUICK_VALUES
    ]
    return InlineKeyboardMarkup([buttons])


# ── Check-in flow ──────────────────────────────────────────────────────────────

async def start_checkin_flow(bot, chat_id: int) -> None:
    """Start evening check-in. Silently skips if one is already in progress."""
    started = checkin_start(chat_id, date.today())
    if not started:
        log.info("Checkin already in progress for %s, skipping duplicate", chat_id)
        return
    await _ask_metric(bot, chat_id)


async def _ask_metric(bot, chat_id: int) -> None:
    state = checkin_get(chat_id)
    if state is None:
        return
    idx, _ = state
    key, label = METRICS[idx]
    text = f"🎯 <b>({idx + 1}/8) {label}</b>\nСколько сегодня?"
    await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=_metric_keyboard(),
        parse_mode="HTML",
    )


async def _process_value(bot, chat_id: int, value: int, query=None) -> None:
    state = checkin_get(chat_id)
    if state is None:
        if query:
            await query.answer("Сессия не найдена. Начни /checkin заново.")
        return

    idx, d = state
    key, label = METRICS[idx]

    upsert_metric(d, key, value)

    ack_text = f"✅ {label}: {value}"
    if query:
        await query.edit_message_text(ack_text, parse_mode="HTML")
    else:
        await bot.send_message(chat_id=chat_id, text=ack_text, parse_mode="HTML")

    next_idx = idx + 1
    if next_idx < len(METRICS):
        checkin_advance(chat_id, next_idx)
        await _ask_metric(bot, chat_id)
    else:
        checkin_end(chat_id)
        summary = daily_summary(d)
        await bot.send_message(chat_id=chat_id, text=summary, parse_mode="HTML")

        if d.weekday() == 6:  # Sunday
            week = get_week_number(d)
            await bot.send_message(
                chat_id=chat_id,
                text=weekly_summary(week),
                parse_mode="HTML",
            )


# ── Command handlers ───────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    save_setting("chat_id", str(chat_id))
    log.info("Registered chat_id: %s", chat_id)
    await update.message.reply_text(
        "👋 <b>Привет!</b> Я бот трекинга воронки коучинга.\n\n"
        "📅 Каждое утро в <b>08:00</b> — дневная норма по плану\n"
        "🌙 Каждый вечер в <b>20:00</b> — ввод данных за день\n"
        "📊 По <b>воскресеньям</b> — итоги недели\n\n"
        "<b>Команды:</b>\n"
        "/checkin — внести данные прямо сейчас\n"
        "/today — что внесено сегодня\n"
        "/stats — утренняя сводка по текущей неделе\n"
        "/week N — данные по неделе N (1–8)",
        parse_mode="HTML",
    )


async def cmd_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    # Reset any stuck state before starting manually
    checkin_end(chat_id)
    await start_checkin_flow(context.bot, chat_id)


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(daily_summary(date.today()), parse_mode="HTML")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(morning_message(), parse_mode="HTML")


async def cmd_week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Использование: /week N  (например: /week 2)")
        return
    n = int(args[0])
    if not 1 <= n <= 8:
        await update.message.reply_text("Неделя должна быть от 1 до 8.")
        return
    await update.message.reply_text(weekly_summary(n), parse_mode="HTML")


# ── Callback & message handlers ────────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("ci_"):
        return

    value = int(query.data[3:])
    await _process_value(context.bot, update.effective_chat.id, value, query=query)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if checkin_get(chat_id) is None:
        return  # Not in check-in mode

    try:
        value = int(update.message.text.strip())
        if value < 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Введи целое неотрицательное число.")
        return

    await _process_value(context.bot, chat_id, value)

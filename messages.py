from datetime import date

from plan import METRICS, PLAN, get_week_number, get_week_dates
from database import get_day, get_week_totals

# Short labels for table columns (fit in Telegram monospace)
SHORT_LABELS = {
    "new_contacts":             "Новые контакты      ",
    "invitations":              "Приглашения         ",
    "signed_up":                "Записались          ",
    "diagnostics_done":         "Диагностики         ",
    "new_clients":              "Нов. клиенты        ",
    "active_clients_coaching":  "АК коучинг          ",
    "active_clients_mentoring": "АК менторинг        ",
    "sessions_done":            "Сессии              ",
}
COL = 20  # label column width


def _label(key: str) -> str:
    return SHORT_LABELS[key]


# ── Morning message ────────────────────────────────────────────────────────────

def morning_message() -> str:
    today = date.today()
    week = get_week_number(today)
    plan = PLAN[week]
    totals = get_week_totals(week)
    w_start, w_end = get_week_dates(week)

    header = (
        f"☀️ <b>Неделя {week}</b>  "
        f"({w_start.strftime('%d.%m')} – {w_end.strftime('%d.%m')})\n\n"
    )

    rows = ["<pre>"]
    rows.append(f"{'Метрика':<20} {'П':>4} {'Факт':>5} {'Ост':>5} {'Н/д':>5}")
    rows.append("─" * 41)

    for key, _ in METRICS:
        plan_val = plan[key]
        done = totals.get(key, 0) or 0
        remaining = max(plan_val - done, 0)
        daily_norm = round(plan_val / 7, 1)
        rows.append(
            f"{_label(key)[:20]:<20} {plan_val:>4} {done:>5} {remaining:>5} {daily_norm:>5}"
        )

    rows.append("</pre>")
    return header + "\n".join(rows)


# ── Daily summary ──────────────────────────────────────────────────────────────

def daily_summary(d: date) -> str:
    row = get_day(d)
    lines = [f"📊 <b>Итог дня {d.strftime('%d.%m.%Y')}:</b>\n"]
    for key, label in METRICS:
        val = (row[key] if row else 0) or 0
        lines.append(f"• {label}: <b>{val}</b>")
    return "\n".join(lines)


# ── Weekly summary ─────────────────────────────────────────────────────────────

def weekly_summary(week: int) -> str:
    plan = PLAN[week]
    totals = get_week_totals(week)
    w_start, w_end = get_week_dates(week)

    header = (
        f"📈 <b>Итоги недели {week}</b>  "
        f"({w_start.strftime('%d.%m')} – {w_end.strftime('%d.%m')})\n\n"
    )

    rows = ["<pre>"]
    rows.append(f"{'Метрика':<20} {'П':>4} {'Факт':>5} {'%':>5}")
    rows.append("─" * 36)

    pcts = []
    for key, _ in METRICS:
        plan_val = plan[key]
        done = totals.get(key, 0) or 0
        pct = round(done / plan_val * 100) if plan_val > 0 else 0
        pcts.append(pct)
        rows.append(f"{_label(key)[:20]:<20} {plan_val:>4} {done:>5} {pct:>4}%")

    rows.append("─" * 36)
    avg = round(sum(pcts) / len(pcts)) if pcts else 0
    rows.append(f"{'Общий %':<20} {'':>4} {'':>5} {avg:>4}%")
    rows.append("</pre>")

    return header + "\n".join(rows)

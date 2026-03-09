from datetime import date

# Project start date: Monday, March 9, 2026
WEEK_START = date(2026, 3, 9)

# 8 tracked metrics: (key, display_label)
METRICS = [
    ("new_contacts",             "Новые контакты"),
    ("invitations",              "Приглашения на диагностику"),
    ("signed_up",                "Записались на диагностику"),
    ("diagnostics_done",         "Проведено диагностик"),
    ("new_clients",              "Новые клиенты"),
    ("active_clients_coaching",  "Активные кл. (коучинг)"),
    ("active_clients_mentoring", "Активные кл. (менторинг)"),
    ("sessions_done",            "Проведено сессий"),
]

METRIC_KEYS = [k for k, _ in METRICS]

# Weekly plan values from Excel (W1–W8)
# sessions_done = active_clients_coaching + active_clients_mentoring
PLAN: dict[int, dict[str, int]] = {
    1: dict(new_contacts=30, invitations=10, signed_up=4, diagnostics_done=3,
            new_clients=1, active_clients_coaching=1, active_clients_mentoring=3, sessions_done=4),
    2: dict(new_contacts=30, invitations=10, signed_up=4, diagnostics_done=3,
            new_clients=1, active_clients_coaching=2, active_clients_mentoring=3, sessions_done=5),
    3: dict(new_contacts=30, invitations=10, signed_up=4, diagnostics_done=3,
            new_clients=1, active_clients_coaching=3, active_clients_mentoring=3, sessions_done=6),
    4: dict(new_contacts=30, invitations=10, signed_up=4, diagnostics_done=3,
            new_clients=1, active_clients_coaching=4, active_clients_mentoring=3, sessions_done=7),
    5: dict(new_contacts=30, invitations=10, signed_up=4, diagnostics_done=3,
            new_clients=1, active_clients_coaching=5, active_clients_mentoring=3, sessions_done=8),
    6: dict(new_contacts=30, invitations=10, signed_up=4, diagnostics_done=3,
            new_clients=1, active_clients_coaching=5, active_clients_mentoring=3, sessions_done=8),
    7: dict(new_contacts=30, invitations=10, signed_up=4, diagnostics_done=3,
            new_clients=1, active_clients_coaching=5, active_clients_mentoring=3, sessions_done=8),
    8: dict(new_contacts=30, invitations=10, signed_up=4, diagnostics_done=3,
            new_clients=1, active_clients_coaching=5, active_clients_mentoring=3, sessions_done=8),
}


def get_week_number(d: date | None = None) -> int:
    """Return current week number (1–8) based on date."""
    if d is None:
        d = date.today()
    delta = (d - WEEK_START).days
    if delta < 0:
        return 1
    return min(delta // 7 + 1, 8)


def get_week_dates(week: int) -> tuple[date, date]:
    """Return (start, end) dates for a given week number."""
    offset = (week - 1) * 7
    start = date(WEEK_START.year, WEEK_START.month, WEEK_START.day)
    from datetime import timedelta
    week_start = start + timedelta(days=offset)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end

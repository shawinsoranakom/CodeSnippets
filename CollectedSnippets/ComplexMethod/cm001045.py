def parse_time_expression(
    time_expr: str | None,
) -> tuple[datetime | None, datetime | None]:
    """
    Parse time expression into datetime range (start, end).

    Supports: "latest", "yesterday", "today", "last week", "last 7 days",
    "last month", "last 30 days", ISO date "YYYY-MM-DD", ISO datetime.
    """
    if not time_expr or time_expr.lower() == "latest":
        return None, None

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    expr = time_expr.lower().strip()

    # Relative time expressions lookup
    relative_times: dict[str, tuple[datetime, datetime]] = {
        "yesterday": (today_start - timedelta(days=1), today_start),
        "today": (today_start, now),
        "last week": (now - timedelta(days=7), now),
        "last 7 days": (now - timedelta(days=7), now),
        "last month": (now - timedelta(days=30), now),
        "last 30 days": (now - timedelta(days=30), now),
    }
    if expr in relative_times:
        return relative_times[expr]

    # Try ISO date format (YYYY-MM-DD)
    date_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", expr)
    if date_match:
        try:
            year, month, day = map(int, date_match.groups())
            start = datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)
            return start, start + timedelta(days=1)
        except ValueError:
            # Invalid date components (e.g., month=13, day=32)
            pass

    # Try ISO datetime
    try:
        parsed = datetime.fromisoformat(expr.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed - timedelta(hours=1), parsed + timedelta(hours=1)
    except ValueError:
        return None, None
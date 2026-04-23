def _round_time(hours: int, minutes: int, seconds: int) -> tuple[int, int, int]:
    """Round time to a lower precision for feedback."""
    if hours > 0:
        # No seconds, round up above 45 minutes and down below 15
        rounded_hours = hours
        rounded_seconds = 0
        if minutes > 45:
            # 01:50:30 -> 02:00:00
            rounded_hours += 1
            rounded_minutes = 0
        elif minutes < 15:
            # 01:10:30 -> 01:00:00
            rounded_minutes = 0
        else:
            # 01:25:30 -> 01:30:00
            rounded_minutes = 30
    elif minutes > 0:
        # Round up above 45 seconds, down below 15
        rounded_hours = 0
        rounded_minutes = minutes
        if seconds > 45:
            # 00:01:50 -> 00:02:00
            rounded_minutes += 1
            rounded_seconds = 0
        elif seconds < 15:
            # 00:01:10 -> 00:01:00
            rounded_seconds = 0
        else:
            # 00:01:25 -> 00:01:30
            rounded_seconds = 30
    else:
        # Round up above 50 seconds, exact below 10, and down to nearest 10
        # otherwise.
        rounded_hours = 0
        rounded_minutes = 0
        if seconds > 50:
            # 00:00:55 -> 00:01:00
            rounded_minutes = 1
            rounded_seconds = 0
        elif seconds < 10:
            # 00:00:09 -> 00:00:09
            rounded_seconds = seconds
        else:
            # 00:01:25 -> 00:01:20
            rounded_seconds = seconds - (seconds % 10)

    return rounded_hours, rounded_minutes, rounded_seconds
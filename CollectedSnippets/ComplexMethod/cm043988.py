def most_recent_quarter(base: date | None = None) -> date:
    """Get the most recent quarter date."""
    if base is None:
        base = date.today()
    base = min(base, date.today())  # This prevents dates from being in the future
    exacts = [(3, 31), (6, 30), (9, 30), (12, 31)]
    for exact in exacts:
        if base.month == exact[0] and base.day == exact[1]:
            return base
    if base.month < 4:
        return date(base.year - 1, 12, 31)
    if base.month < 7:
        return date(base.year, 3, 31)
    if base.month < 10:
        return date(base.year, 6, 30)
    return date(base.year, 9, 30)
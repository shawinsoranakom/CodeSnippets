def _date_to_datetime(date_: date) -> datetime:
    return datetime.combine(date_, time())
def _parse_yyyymmdd_str(date_str: str) -> datetime.datetime:
    year, month, day = [int(token) for token in date_str.split("-", 2)]
    return datetime.datetime(year, month, day)
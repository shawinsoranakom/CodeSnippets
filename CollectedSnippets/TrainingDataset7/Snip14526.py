def parse_http_date_safe(date):
    """
    Same as parse_http_date, but return None if the input is invalid.
    """
    try:
        return parse_http_date(date)
    except Exception:
        pass
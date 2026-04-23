def _get_decimal_column(data):
    if data["max_digits"] is None and data["decimal_places"] is None:
        return "numeric"
    return "numeric(%(max_digits)s, %(decimal_places)s)" % data
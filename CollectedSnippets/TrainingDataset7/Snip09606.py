def _get_decimal_column(data):
    if data["max_digits"] is None and data["decimal_places"] is None:
        return "NUMBER"
    return "NUMBER(%(max_digits)s, %(decimal_places)s)" % data
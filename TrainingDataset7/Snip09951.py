def _get_varchar_column(data):
    if data["max_length"] is None:
        return "varchar"
    return "varchar(%(max_length)s)" % data
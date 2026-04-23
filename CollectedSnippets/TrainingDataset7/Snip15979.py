def callable_year(dt_value):
    try:
        return dt_value.year
    except AttributeError:
        return None
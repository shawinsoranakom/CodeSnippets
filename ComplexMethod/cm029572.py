def _localize(formatted, grouping=False, monetary=False):
    # floats and decimal ints need special action!
    if '.' in formatted:
        seps = 0
        parts = formatted.split('.')
        if grouping:
            parts[0], seps = _group(parts[0], monetary=monetary)
        decimal_point = localeconv()[monetary and 'mon_decimal_point'
                                              or 'decimal_point']
        formatted = decimal_point.join(parts)
        if seps:
            formatted = _strip_padding(formatted, seps)
    else:
        seps = 0
        if grouping:
            formatted, seps = _group(formatted, monetary=monetary)
        if seps:
            formatted = _strip_padding(formatted, seps)
    return formatted
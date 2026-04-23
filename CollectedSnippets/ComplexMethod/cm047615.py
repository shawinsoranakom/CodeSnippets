def _value_to_date(value, env, iso_only=False):
    # check datetime first, because it's a subclass of date
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date) or value is False:
        return value
    if isinstance(value, str):
        if iso_only:
            try:
                value = parse_iso_date(value)
            except ValueError:
                # check format
                parse_date(value, env)
                return value
        else:
            value = parse_date(value, env)
        return _value_to_date(value, env)
    if isinstance(value, COLLECTION_TYPES):
        return OrderedSet(_value_to_date(v, env=env, iso_only=iso_only) for v in value)
    if isinstance(value, SQL):
        warnings.warn("Since 19.0, use Domain.custom(to_sql=lambda model, alias, query: SQL(...))", DeprecationWarning)
        return value
    raise ValueError(f'Failed to cast {value!r} into a date')
def _value_to_datetime(value, env, iso_only=False):
    """Convert a value(s) to datetime.

    :returns: A tuple containing the converted value and a boolean indicating
              that all input values were dates.
              These are handled differently during rewrites.
    """
    if isinstance(value, datetime):
        if value.tzinfo:
            # cast to a naive datetime
            warnings.warn("Use naive datetimes in domains")
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value, False
    if value is False:
        return False, True
    if isinstance(value, str):
        if iso_only:
            try:
                value = parse_iso_date(value)
            except ValueError:
                # check formatting
                _dt, is_date = _value_to_datetime(parse_date(value, env), env)
                return value, is_date
        else:
            value = parse_date(value, env)
        return _value_to_datetime(value, env)
    if isinstance(value, date):
        if value.year in (1, 9999):
            # avoid overflow errors, treat as UTC timezone
            tz = None
        elif (tz := env.tz) != pytz.utc:
            # get the tzinfo (without LMT)
            tz = tz.localize(datetime.combine(value, time.min)).tzinfo
        else:
            tz = None
        value = datetime.combine(value, time.min, tz)
        if tz is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value, True
    if isinstance(value, COLLECTION_TYPES):
        value, is_date = zip(*(_value_to_datetime(v, env=env, iso_only=iso_only) for v in value))
        return OrderedSet(value), all(is_date)
    if isinstance(value, SQL):
        warnings.warn("Since 19.0, use Domain.custom(to_sql=lambda model, alias, query: SQL(...))", DeprecationWarning)
        return value, False
    raise ValueError(f'Failed to cast {value!r} into a datetime')
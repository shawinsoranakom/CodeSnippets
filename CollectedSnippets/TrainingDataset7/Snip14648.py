def _datetime_ambiguous_or_imaginary(dt, tz):
    return tz.utcoffset(dt.replace(fold=not dt.fold)) != tz.utcoffset(dt)
def localize(value, use_l10n=None):
    """
    Check if value is a localizable type (date, number...) and return it
    formatted as a string using current locale format.

    If use_l10n is provided and is not None, it forces the value to
    be localized (or not), otherwise it's always localized.
    """
    if isinstance(value, str):  # Handle strings first for performance reasons.
        return value
    elif isinstance(value, bool):  # Make sure booleans don't get treated as numbers
        return str(value)
    elif isinstance(value, (decimal.Decimal, float, int)):
        if use_l10n is False:
            return str(value)
        return number_format(value, use_l10n=use_l10n)
    elif isinstance(value, datetime.datetime):
        return date_format(value, "DATETIME_FORMAT", use_l10n=use_l10n)
    elif isinstance(value, datetime.date):
        return date_format(value, use_l10n=use_l10n)
    elif isinstance(value, datetime.time):
        return time_format(value, use_l10n=use_l10n)
    return value
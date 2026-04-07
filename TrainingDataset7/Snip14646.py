def make_aware(value, timezone=None):
    """Make a naive datetime.datetime in a given time zone aware."""
    if timezone is None:
        timezone = get_current_timezone()
    # Check that we won't overwrite the timezone of an aware datetime.
    if is_aware(value):
        raise ValueError("make_aware expects a naive datetime, got %s" % value)
    # This may be wrong around DST changes!
    return value.replace(tzinfo=timezone)
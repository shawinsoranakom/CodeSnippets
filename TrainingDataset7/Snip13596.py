def localtime(value):
    """
    Convert a datetime to local time in the active time zone.

    This only makes sense within a {% localtime off %} block.
    """
    return do_timezone(value, timezone.get_current_timezone())
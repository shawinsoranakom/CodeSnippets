def _get_latest_lastmod(current_lastmod, new_lastmod):
    """
    Returns the latest `lastmod` where `lastmod` can be either a date or a
    datetime.
    """
    if not isinstance(new_lastmod, datetime.datetime):
        new_lastmod = datetime.datetime.combine(new_lastmod, datetime.time.min)
    if timezone.is_naive(new_lastmod):
        new_lastmod = timezone.make_aware(new_lastmod, datetime.UTC)
    return new_lastmod if current_lastmod is None else max(current_lastmod, new_lastmod)
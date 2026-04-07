def urlencode(value, safe=None):
    """
    Escape a value for use in a URL.

    The ``safe`` parameter determines the characters which should not be
    escaped by Python's quote() function. If not provided, use the default safe
    characters (but an empty string can be provided when *all* characters
    should be escaped).
    """
    kwargs = {}
    if safe is not None:
        kwargs["safe"] = safe
    return quote(value, **kwargs)
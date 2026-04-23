def get_max_age(response):
    """
    Return the max-age from the response Cache-Control header as an integer,
    or None if it wasn't found or wasn't an integer.
    """
    if not response.has_header("Cache-Control"):
        return
    cc = dict(
        _to_tuple(el) for el in cc_delim_re.split(response.headers["Cache-Control"])
    )
    try:
        return int(cc["max-age"])
    except (ValueError, TypeError, KeyError):
        pass
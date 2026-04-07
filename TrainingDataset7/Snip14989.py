def was_modified_since(header=None, mtime=0):
    """
    Was something modified since the user last downloaded it?

    header
      This is the value of the If-Modified-Since header. If this is None,
      I'll just return True.

    mtime
      This is the modification time of the item we're talking about.
    """
    try:
        if header is None:
            raise ValueError
        header_mtime = parse_http_date(header)
        if int(mtime) > header_mtime:
            raise ValueError
    except (ValueError, OverflowError):
        return True
    return False
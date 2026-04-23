def unquote(s):
    """Undo the effects of quote()."""
    return UNQUOTE_RE.sub(lambda m: UNQUOTE_MAP[m[0]], s)
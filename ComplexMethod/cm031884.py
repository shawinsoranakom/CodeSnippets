def _resolve_max_size(filename, maxsizes):
    for pattern, maxsize in (maxsizes.items() if maxsizes else ()):
        if _match_glob(filename, pattern):
            break
    else:
        return None
    if not maxsize:
        return None, None
    maxtext, maxlines = maxsize
    if maxtext is not None:
        maxtext = int(maxtext)
    if maxlines is not None:
        maxlines = int(maxlines)
    return maxtext, maxlines
def _compile(pattern, flags):
    # internal: compile pattern
    if isinstance(flags, RegexFlag):
        flags = flags.value
    try:
        return _cache2[type(pattern), pattern, flags]
    except KeyError:
        pass

    key = (type(pattern), pattern, flags)
    # Item in _cache should be moved to the end if found.
    p = _cache.pop(key, None)
    if p is None:
        if isinstance(pattern, Pattern):
            if flags:
                raise ValueError(
                    "cannot process flags argument with a compiled pattern")
            return pattern
        if not _compiler.isstring(pattern):
            raise TypeError("first argument must be string or compiled pattern")
        p = _compiler.compile(pattern, flags)
        if flags & DEBUG:
            return p
        if len(_cache) >= _MAXCACHE:
            # Drop the least recently used item.
            # next(iter(_cache)) is known to have linear amortized time,
            # but it is used here to avoid a dependency from using OrderedDict.
            # For the small _MAXCACHE value it doesn't make much of a difference.
            try:
                del _cache[next(iter(_cache))]
            except (StopIteration, RuntimeError, KeyError):
                pass
    # Append to the end.
    _cache[key] = p

    if len(_cache2) >= _MAXCACHE2:
        # Drop the oldest item.
        try:
            del _cache2[next(iter(_cache2))]
        except (StopIteration, RuntimeError, KeyError):
            pass
    _cache2[key] = p
    return p
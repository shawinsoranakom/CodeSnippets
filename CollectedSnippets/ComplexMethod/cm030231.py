def cmp(f1, f2, shallow=True):
    """Compare two files.

    Arguments:

    f1 -- First file name

    f2 -- Second file name

    shallow -- treat files as identical if their stat signatures (type, size,
               mtime) are identical. Otherwise, files are considered different
               if their sizes or contents differ.  [default: True]

    Return value:

    True if the files are the same, False otherwise.

    This function uses a cache for past comparisons and the results,
    with cache entries invalidated if their stat information
    changes.  The cache may be cleared by calling clear_cache().

    """

    s1 = _sig(os.stat(f1))
    s2 = _sig(os.stat(f2))
    if s1[0] != stat.S_IFREG or s2[0] != stat.S_IFREG:
        return False
    if shallow and s1 == s2:
        return True
    if s1[1] != s2[1]:
        return False

    outcome = _cache.get((f1, f2, s1, s2))
    if outcome is None:
        outcome = _do_cmp(f1, f2)
        if len(_cache) > 100:      # limit the maximum size of the cache
            clear_cache()
        _cache[f1, f2, s1, s2] = outcome
    return outcome
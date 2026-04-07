def find(path, find_all=False):
    """
    Find a static file with the given path using all enabled finders.

    If ``find_all`` is ``False`` (default), return the first matching
    absolute path (or ``None`` if no match). Otherwise return a list.
    """
    searched_locations[:] = []
    matches = []
    for finder in get_finders():
        result = finder.find(path, find_all=find_all)
        if not find_all and result:
            return result
        if not isinstance(result, (list, tuple)):
            result = [result]
        matches.extend(result)
    if matches:
        return matches
    # No match.
    return [] if find_all else None
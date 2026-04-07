def matches_patterns(path, patterns):
    """
    Return True or False depending on whether the ``path`` should be
    ignored (if it matches any pattern in ``ignore_patterns``).
    """
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)
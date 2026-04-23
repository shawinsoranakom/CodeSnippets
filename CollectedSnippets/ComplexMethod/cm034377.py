def pfilter(f, patterns=None, excludes=None, use_regex=False):
    """filter using glob patterns"""
    if not patterns and not excludes:
        return True

    if use_regex:
        if patterns and not excludes:
            for p in patterns:
                r = re.compile(p)
                if r.match(f):
                    return True

        elif patterns and excludes:
            for p in patterns:
                r = re.compile(p)
                if r.match(f):
                    for e in excludes:
                        r = re.compile(e)
                        if r.match(f):
                            return False
                    return True

    else:
        if patterns and not excludes:
            for p in patterns:
                if fnmatch.fnmatch(f, p):
                    return True

        elif patterns and excludes:
            for p in patterns:
                if fnmatch.fnmatch(f, p):
                    for e in excludes:
                        if fnmatch.fnmatch(f, e):
                            return False
                    return True

    return False
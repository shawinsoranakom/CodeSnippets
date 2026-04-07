def _sqlite_regexp(pattern, string):
    if pattern is None or string is None:
        return None
    if not isinstance(string, str):
        string = str(string)
    return bool(re_search(pattern, string))
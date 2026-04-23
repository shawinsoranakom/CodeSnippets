def patterns_to_regex(allowed_patterns: list[str]) -> Any:
    """
    pattern is glob-like, i.e. the only special sequences it has are:
      - ? - matches single character
      - * - matches any non-folder separator characters or no character
      - ** - matches any characters or no character
      Assuming that patterns are free of braces and backslashes
      the only character that needs to be escaped are dot and plus
    """
    rc = "("
    for idx, pattern in enumerate(allowed_patterns):
        if idx > 0:
            rc += "|"
        pattern_ = PeekableIterator(pattern)
        if any(c in pattern for c in "{}()[]\\"):
            raise AssertionError(
                f"Pattern contains invalid characters (braces/parens/brackets/backslash): {pattern}"
            )
        for c in pattern_:
            if c == ".":
                rc += "\\."
            elif c == "+":
                rc += "\\+"
            elif c == "*":
                if pattern_.peek() == "*":
                    next(pattern_)
                    rc += ".*"
                else:
                    rc += "[^/]*"
            else:
                rc += c
    rc += ")"
    return re.compile(rc)
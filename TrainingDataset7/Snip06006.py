def replace_metacharacters(pattern):
    """Remove unescaped metacharacters from the pattern."""
    return re.sub(
        r"((?:^|(?<!\\))(?:\\\\)*)(\\?)([?*+^$]|\\[bBAZ])",
        lambda m: m[1] + m[3] if m[2] else m[1],
        pattern,
    )
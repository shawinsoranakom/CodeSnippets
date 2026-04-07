def normalize_spaces(val):
    """Convert multiple spaces to single and strip from both sides."""
    if not (val := val.strip()):
        return None
    return multiple_spaces_re.sub(" ", val)
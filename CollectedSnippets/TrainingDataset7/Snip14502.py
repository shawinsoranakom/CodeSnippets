def strip_spaces_between_tags(value):
    """Return the given HTML with spaces between tags removed."""
    return re.sub(r">\s+<", "><", str(value))
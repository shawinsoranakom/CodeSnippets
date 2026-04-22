def is_altair_chart(obj: object) -> bool:
    """True if input looks like an Altair chart."""
    return is_type(obj, _ALTAIR_RE)
def escapejs(value):
    """Hex encode characters for use in JavaScript strings."""
    return mark_safe(str(value).translate(_js_escapes))
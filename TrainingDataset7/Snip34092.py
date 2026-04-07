def noop(value, param=None):
    """A noop filter that always return its first argument and does nothing
    with its second (optional) one. Useful for testing out whitespace in filter
    arguments (see #19882)."""
    return value
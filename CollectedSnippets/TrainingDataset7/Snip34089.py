def make_data_div(value):
    """A filter that uses a decorator (@mark_safe)."""
    return '<div data-name="%s"></div>' % value
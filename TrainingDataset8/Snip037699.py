def get_instance() -> Runtime:
    """Return the singleton Runtime instance. Raise an Error if the
    Runtime hasn't been created yet.
    """
    return Runtime.instance()
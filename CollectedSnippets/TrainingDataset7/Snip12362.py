def get_autocommit(using=None):
    """Get the autocommit status of the connection."""
    return get_connection(using).get_autocommit()
def set_autocommit(autocommit, using=None):
    """Set the autocommit status of the connection."""
    return get_connection(using).set_autocommit(autocommit)
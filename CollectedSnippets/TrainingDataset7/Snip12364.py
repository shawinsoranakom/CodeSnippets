def commit(using=None):
    """Commit a transaction."""
    get_connection(using).commit()
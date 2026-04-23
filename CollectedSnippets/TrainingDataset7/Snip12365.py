def rollback(using=None):
    """Roll back a transaction."""
    get_connection(using).rollback()
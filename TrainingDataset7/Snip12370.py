def get_rollback(using=None):
    """Get the "needs rollback" flag -- for *advanced use* only."""
    return get_connection(using).get_rollback()
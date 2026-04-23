def on_commit(func, using=None, robust=False):
    """
    Register `func` to be called when the current transaction is committed.
    If the current transaction is rolled back, `func` will not be called.
    """
    get_connection(using).on_commit(func, robust)
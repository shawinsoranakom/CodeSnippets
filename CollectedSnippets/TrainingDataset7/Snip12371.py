def set_rollback(rollback, using=None):
    """
    Set or unset the "needs rollback" flag -- for *advanced use* only.

    When `rollback` is `True`, trigger a rollback when exiting the innermost
    enclosing atomic block that has `savepoint=True` (that's the default). Use
    this to force a rollback without raising an exception.

    When `rollback` is `False`, prevent such a rollback. Use this only after
    rolling back to a known-good state! Otherwise, you break the atomic block
    and data corruption may occur.
    """
    return get_connection(using).set_rollback(rollback)
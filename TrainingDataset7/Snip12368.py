def savepoint_commit(sid, using=None):
    """
    Commit the most recent savepoint (if one exists). Do nothing if
    savepoints are not supported.
    """
    get_connection(using).savepoint_commit(sid)
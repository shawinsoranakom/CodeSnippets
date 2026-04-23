def savepoint(using=None):
    """
    Create a savepoint (if supported and required by the backend) inside the
    current transaction. Return an identifier for the savepoint that will be
    used for the subsequent rollback or commit.
    """
    return get_connection(using).savepoint()
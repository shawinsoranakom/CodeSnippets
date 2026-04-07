def connections_support_transactions(aliases=None):
    """
    Return whether or not all (or specified) connections support
    transactions.
    """
    conns = (
        connections.all()
        if aliases is None
        else (connections[alias] for alias in aliases)
    )
    return all(conn.features.supports_transactions for conn in conns)
def connections_support_savepoints(aliases=None):
    """
    Return whether or not all (or specified) connections support savepoints.
    """
    conns = (
        connections.all()
        if aliases is None
        else (connections[alias] for alias in aliases)
    )
    return all(conn.features.uses_savepoints for conn in conns)
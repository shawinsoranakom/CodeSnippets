def reset_queries(**kwargs):
    for conn in connections.all(initialized_only=True):
        conn.queries_log.clear()
def _make_connections_override(cls):
        connections_override = {}
        for conn in connections.all():
            # If using in-memory sqlite databases, pass the connections to
            # the server thread.
            if conn.vendor == "sqlite" and conn.is_in_memory_db():
                connections_override[conn.alias] = conn
        return connections_override
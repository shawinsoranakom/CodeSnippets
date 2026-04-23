def _make_connections_override(cls):
        conn = connections[DEFAULT_DB_ALIAS]
        cls.conn = conn
        cls.old_conn_max_age = conn.settings_dict["CONN_MAX_AGE"]
        # Set the connection's CONN_MAX_AGE to None to simulate the
        # CONN_MAX_AGE setting being set to None on the server. This prevents
        # Django from closing the connection and allows testing that
        # ThreadedWSGIServer closes connections.
        conn.settings_dict["CONN_MAX_AGE"] = None
        # Pass a database connection through to the server to check it is being
        # closed by ThreadedWSGIServer.
        return {DEFAULT_DB_ALIAS: conn}
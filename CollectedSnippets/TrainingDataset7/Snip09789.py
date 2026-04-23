def _configure_connection(self, connection):
        # This function is called from init_connection_state and from the
        # psycopg pool itself after a connection is opened.

        # Commit after setting the time zone.
        commit_tz = self._configure_timezone(connection)
        # Set the role on the connection. This is useful if the credential used
        # to login is not the same as the role that owns database resources. As
        # can be the case when using temporary or ephemeral credentials.
        commit_role = self._configure_role(connection)

        return commit_role or commit_tz
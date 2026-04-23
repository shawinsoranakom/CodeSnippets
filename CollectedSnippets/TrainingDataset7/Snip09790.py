def _close(self):
        if self.connection is not None:
            # `wrap_database_errors` only works for `putconn` as long as there
            # is no `reset` function set in the pool because it is deferred
            # into a thread and not directly executed.
            with self.wrap_database_errors:
                if self.pool:
                    # Ensure the correct pool is returned. This is a workaround
                    # for tests so a pool can be changed on setting changes
                    # (e.g. USE_TZ, TIME_ZONE).
                    self.connection._pool.putconn(self.connection)
                    # Connection can no longer be used.
                    self.connection = None
                else:
                    return self.connection.close()
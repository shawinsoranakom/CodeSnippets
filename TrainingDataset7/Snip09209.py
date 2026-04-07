def temporary_connection(self):
        """
        Context manager that ensures that a connection is established, and
        if it opened one, closes it to avoid leaving a dangling connection.
        This is useful for operations outside of the request-response cycle.

        Provide a cursor: with self.temporary_connection() as cursor: ...
        """
        must_close = self.connection is None
        try:
            with self.cursor() as cursor:
                yield cursor
        finally:
            if must_close:
                self.close()
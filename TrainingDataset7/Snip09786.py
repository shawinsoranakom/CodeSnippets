def ensure_timezone(self):
        # Close the pool so new connections pick up the correct timezone.
        self.close_pool()
        if self.connection is None:
            return False
        return self._configure_timezone(self.connection)
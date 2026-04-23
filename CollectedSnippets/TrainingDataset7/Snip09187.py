def get_autocommit(self):
        """Get the autocommit state."""
        self.ensure_connection()
        return self.autocommit
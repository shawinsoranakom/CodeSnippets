def fetch_mode(self, fetch_mode):
        """Set the fetch mode for the QuerySet."""
        clone = self._chain()
        clone._fetch_mode = fetch_mode
        return clone
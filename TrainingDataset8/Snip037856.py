def get_current(cls):
        """Return the singleton instance."""
        if cls._singleton is None:
            Credentials()

        return Credentials._singleton
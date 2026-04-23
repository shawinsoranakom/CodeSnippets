def create_cursor(self, name=None):
        """Create a cursor. Assume that a connection is established."""
        raise NotImplementedError(
            "subclasses of BaseDatabaseWrapper may require a create_cursor() method"
        )
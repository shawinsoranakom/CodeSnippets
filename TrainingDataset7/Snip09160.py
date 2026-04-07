def get_database_version(self):
        """Return a tuple of the database's version."""
        raise NotImplementedError(
            "subclasses of BaseDatabaseWrapper may require a get_database_version() "
            "method."
        )
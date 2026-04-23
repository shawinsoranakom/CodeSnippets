def _set_autocommit(self, autocommit):
        """
        Backend-specific implementation to enable or disable autocommit.
        """
        raise NotImplementedError(
            "subclasses of BaseDatabaseWrapper may require a _set_autocommit() method"
        )
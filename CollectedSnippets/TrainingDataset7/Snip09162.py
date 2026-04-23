def get_connection_params(self):
        """Return a dict of parameters suitable for get_new_connection."""
        raise NotImplementedError(
            "subclasses of BaseDatabaseWrapper may require a get_connection_params() "
            "method"
        )
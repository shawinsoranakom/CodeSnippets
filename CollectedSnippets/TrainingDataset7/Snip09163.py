def get_new_connection(self, conn_params):
        """Open a connection to the database."""
        raise NotImplementedError(
            "subclasses of BaseDatabaseWrapper may require a get_new_connection() "
            "method"
        )
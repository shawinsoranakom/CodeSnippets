def wrap_database_errors(self):
        """
        Context manager and decorator that re-throws backend-specific database
        exceptions using Django's common wrappers.
        """
        return DatabaseErrorWrapper(self)
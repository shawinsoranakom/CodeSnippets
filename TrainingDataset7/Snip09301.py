def quote_name(self, name):
        """
        Return a quoted version of the given table, index, or column name. Do
        not quote the given name if it's already been quoted.
        """
        raise NotImplementedError(
            "subclasses of BaseDatabaseOperations may require a quote_name() method"
        )
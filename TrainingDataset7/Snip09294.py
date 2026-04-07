def no_limit_value(self):
        """
        Return the value to use for the LIMIT when we are wanting "LIMIT
        infinity". Return None if the limit clause can be omitted in this case.
        """
        raise NotImplementedError(
            "subclasses of BaseDatabaseOperations may require a no_limit_value() method"
        )
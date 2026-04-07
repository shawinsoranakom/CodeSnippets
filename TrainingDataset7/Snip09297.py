def process_clob(self, value):
        """
        Return the value of a CLOB column, for backends that return a locator
        object that requires additional processing.
        """
        return value
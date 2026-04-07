def adapt_ipaddressfield_value(self, value):
        """
        Transform a string representation of an IP address into the expected
        type for the backend driver.
        """
        return value or None
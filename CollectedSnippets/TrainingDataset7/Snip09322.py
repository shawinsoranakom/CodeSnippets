def adapt_decimalfield_value(self, value, max_digits=None, decimal_places=None):
        """
        Transform a decimal.Decimal value to an object compatible with what is
        expected by the backend driver for decimal (numeric) columns.
        """
        return value
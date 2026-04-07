def _create_decimal(value):
        if isinstance(value, (int, str)):
            return decimal.Decimal(value)
        return decimal.Context(prec=15).create_decimal_from_float(value)
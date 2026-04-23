def get_decimalfield_converter(self, expression):
        # SQLite stores only 15 significant digits. Digits coming from
        # float inaccuracy must be removed.
        if isinstance(expression, Col):
            quantize_value = decimal.Decimal(1).scaleb(
                -expression.output_field.decimal_places
            )

            def converter(value, expression, connection):
                if value is not None:
                    return self._create_decimal(value).quantize(
                        quantize_value, context=expression.output_field.context
                    )

        else:

            def converter(value, expression, connection):
                if value is not None:
                    return self._create_decimal(value)

        return converter
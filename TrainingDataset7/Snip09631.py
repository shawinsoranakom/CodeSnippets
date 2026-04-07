def _output_number_converter(value):
        return decimal.Decimal(value) if "." in value else int(value)
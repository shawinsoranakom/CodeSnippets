def _get_decimal_converter(precision, scale):
        if scale == 0:
            return int
        context = decimal.Context(prec=precision)
        quantize_value = decimal.Decimal(1).scaleb(-scale)
        return lambda v: decimal.Decimal(v).quantize(quantize_value, context=context)
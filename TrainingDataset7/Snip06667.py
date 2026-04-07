def __init__(self, expr):
        super().__init__(expr)
        expr = self.source_expressions[0]
        if isinstance(expr, Value) and not expr._output_field_or_none:
            self.source_expressions[0] = Value(
                expr.value, output_field=RasterField(srid=expr.value.srid)
            )
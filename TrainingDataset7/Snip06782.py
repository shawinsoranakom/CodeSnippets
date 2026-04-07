def __init__(self, *expressions, **extra):
        super().__init__(*expressions, **extra)

        # Ensure that value expressions are geometric.
        for pos in self.geom_param_pos:
            expr = self.source_expressions[pos]
            if not isinstance(expr, Value):
                continue
            try:
                output_field = expr.output_field
            except FieldError:
                output_field = None
            geom = expr.value
            if (
                not isinstance(geom, GEOSGeometry)
                or output_field
                and not isinstance(output_field, GeometryField)
            ):
                raise TypeError(
                    "%s function requires a geometric argument in position %d."
                    % (self.name, pos + 1)
                )
            if not geom.srid and not output_field:
                raise ValueError("SRID is required for all geometries.")
            if not output_field:
                self.source_expressions[pos] = Value(
                    geom, output_field=GeometryField(srid=geom.srid)
                )
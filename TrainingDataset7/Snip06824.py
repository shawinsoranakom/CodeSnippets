def __init__(self, expression, srid, **extra):
        expressions = [
            expression,
            self._handle_param(srid, "srid", int),
        ]
        if "output_field" not in extra:
            extra["output_field"] = GeometryField(srid=srid)
        super().__init__(*expressions, **extra)
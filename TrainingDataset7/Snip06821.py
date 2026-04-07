def __init__(self, expression, angle, origin=None, **extra):
        expressions = [
            expression,
            self._handle_param(angle, "angle", NUMERIC_TYPES),
        ]
        if origin is not None:
            if not isinstance(origin, Point):
                raise TypeError("origin argument must be a Point")
            expressions.append(Value(origin.wkt, output_field=GeometryField()))
        super().__init__(*expressions, **extra)
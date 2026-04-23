def __init__(self, expression, x, y, z=0.0, **extra):
        expressions = [
            expression,
            self._handle_param(x, "x", NUMERIC_TYPES),
            self._handle_param(y, "y", NUMERIC_TYPES),
        ]
        if z != 0.0:
            expressions.append(self._handle_param(z, "z", NUMERIC_TYPES))
        super().__init__(*expressions, **extra)
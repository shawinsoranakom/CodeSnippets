def __init__(self, expression, version=2, precision=8, **extra):
        expressions = [version, expression]
        if precision is not None:
            expressions.append(self._handle_param(precision, "precision", int))
        super().__init__(*expressions, **extra)
def __init__(self, expression, relative=False, precision=8, **extra):
        relative = (
            relative if hasattr(relative, "resolve_expression") else int(relative)
        )
        expressions = [
            expression,
            relative,
            self._handle_param(precision, "precision", int),
        ]
        super().__init__(*expressions, **extra)
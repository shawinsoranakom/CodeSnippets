def __init__(self, expression, *, output_field=None, **extra):
        super().__init__(
            expression, output_field=output_field or DecimalField(), **extra
        )
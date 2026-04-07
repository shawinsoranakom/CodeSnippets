def __init__(self, expression, **extra):
        super().__init__(expression, output_field=ExtentField(), **extra)
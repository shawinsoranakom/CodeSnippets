def __init__(self, *expressions, **extra):
        if len(expressions) < 2:
            raise ValueError("Concat must take at least two expressions")
        paired = self._paired(expressions, output_field=extra.get("output_field"))
        super().__init__(paired, **extra)
def __init__(self, *expressions, **extra):
        if len(expressions) < 2:
            raise ValueError("Greatest must take at least two expressions")
        super().__init__(*expressions, **extra)
def __init__(self, string, expression, **extra):
        if not hasattr(string, "resolve_expression"):
            string = Value(string)
        super().__init__(string, expression, **extra)
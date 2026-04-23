def __init__(self, expression, string, **extra):
        if not hasattr(string, "resolve_expression"):
            string = Value(string)
        super().__init__(expression, string, **extra)
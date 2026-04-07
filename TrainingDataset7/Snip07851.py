def __init__(self, *expressions, config=None, weight=None):
        super().__init__(*expressions)
        self.config = SearchConfig.from_parameter(config)
        if weight is not None and not hasattr(weight, "resolve_expression"):
            weight = Value(weight)
        self.weight = weight
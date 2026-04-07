def __init__(self, config):
        super().__init__()
        if not hasattr(config, "resolve_expression"):
            config = Value(config)
        self.config = config
def __init__(self, alias, params):
        super().__init__(alias, params)
        self.prefix = self.options.get("prefix", "")
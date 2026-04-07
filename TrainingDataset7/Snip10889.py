def __init__(self, alias, targets, sources, output_field):
        super().__init__(output_field=output_field)
        self.alias = alias
        self.targets = targets
        self.sources = sources
def __init__(self, lhs, connector, rhs, config, output_field=None):
        self.config = config
        super().__init__(lhs, connector, rhs, output_field)
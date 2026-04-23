def set_source_expressions(self, exprs):
        assert all(isinstance(expr, Col) and expr.alias == self.alias for expr in exprs)
        self.targets = [col.target for col in exprs]
        self.sources = [col.field for col in exprs]
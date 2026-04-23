def allowed_default(self):
        return all(expression.allowed_default for expression in self.source_expressions)
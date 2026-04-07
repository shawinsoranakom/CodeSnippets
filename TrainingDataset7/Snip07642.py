def check(self, model, connection):
        errors = super().check(model, connection)
        references = set()
        for expr, _ in self.expressions:
            if isinstance(expr, str):
                expr = F(expr)
            references.update(model._get_expr_references(expr))
        errors.extend(self._check_references(model, references))
        return errors
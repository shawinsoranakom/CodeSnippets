def _subquery_fields_len(self):
        if not self.has_select_fields or not self.select:
            return len(self.model._meta.pk_fields)
        return len(self.select) + sum(
            len(expr.targets) - 1 for expr in self.select if isinstance(expr, ColPairs)
        )
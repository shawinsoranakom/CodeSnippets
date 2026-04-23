def get_group_by_cols(self):
        if isinstance(self.expression, Expression):
            expression = self.expression.copy()
            expression.output_field = self.output_field
            return expression.get_group_by_cols()
        # For non-expressions e.g. an SQL WHERE clause, the entire
        # `expression` must be included in the GROUP BY clause.
        return super().get_group_by_cols()
def conditional_expression_supported_in_where_clause(self, expression):
        # MySQL ignores indexes with boolean fields unless they're compared
        # directly to a boolean value.
        if isinstance(expression, (Exists, Lookup)):
            return True
        if isinstance(expression, ExpressionWrapper) and expression.conditional:
            return self.conditional_expression_supported_in_where_clause(
                expression.expression
            )
        if getattr(expression, "conditional", False):
            return False
        return super().conditional_expression_supported_in_where_clause(expression)
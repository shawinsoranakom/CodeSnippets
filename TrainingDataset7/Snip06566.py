def check_expression_support(self, expression):
        if isinstance(expression, self.disallowed_aggregates):
            raise NotSupportedError(
                "%s spatial aggregation is not supported by this database backend."
                % expression.name
            )
        super().check_expression_support(expression)
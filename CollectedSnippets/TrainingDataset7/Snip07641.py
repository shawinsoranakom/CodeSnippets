def _get_expressions(self, schema_editor, query):
        expressions = []
        for idx, (expression, operator) in enumerate(self.expressions):
            if isinstance(expression, str):
                expression = F(expression)
            expression = ExclusionConstraintExpression(expression, operator=operator)
            expression.set_wrapper_classes(schema_editor.connection)
            expressions.append(expression)
        return ExpressionList(*expressions).resolve_expression(query)
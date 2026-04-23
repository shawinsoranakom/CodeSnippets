def _get_index_expressions(self, model, schema_editor):
        if not self.expressions:
            return None
        index_expressions = []
        for expression in self.expressions:
            index_expression = IndexExpression(expression)
            index_expression.set_wrapper_classes(schema_editor.connection)
            index_expressions.append(index_expression)
        return ExpressionList(*index_expressions).resolve_expression(
            Query(model, alias_cols=False),
        )
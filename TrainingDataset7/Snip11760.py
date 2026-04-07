def create_sql(self, model, schema_editor, using="", **kwargs):
        include = [
            model._meta.get_field(field_name).column for field_name in self.include
        ]
        condition = self._get_condition_sql(model, schema_editor)
        if self.expressions:
            index_expressions = []
            for expression in self.expressions:
                index_expression = IndexExpression(expression)
                index_expression.set_wrapper_classes(schema_editor.connection)
                index_expressions.append(index_expression)
            expressions = ExpressionList(*index_expressions).resolve_expression(
                Query(model, alias_cols=False),
            )
            fields = None
            col_suffixes = None
        else:
            fields = [
                model._meta.get_field(field_name)
                for field_name, _ in self.fields_orders
            ]
            if schema_editor.connection.features.supports_index_column_ordering:
                col_suffixes = [order[1] for order in self.fields_orders]
            else:
                col_suffixes = [""] * len(self.fields_orders)
            expressions = None
        return schema_editor._create_index_sql(
            model,
            fields=fields,
            name=self.name,
            using=using,
            db_tablespace=self.db_tablespace,
            col_suffixes=col_suffixes,
            opclasses=self.opclasses,
            condition=condition,
            include=include,
            expressions=expressions,
            **kwargs,
        )
def as_sql(self, compiler, connection, template=None, **extra_context):
        if isinstance(self.expression, ColPairs):
            sql_parts = []
            params = []
            for col in self.expression.get_cols():
                copy = self.copy()
                copy.set_source_expressions([col])
                sql, col_params = compiler.compile(copy)
                sql_parts.append(sql)
                params.extend(col_params)
            return ", ".join(sql_parts), params
        template = template or self.template
        if connection.features.supports_order_by_nulls_modifier:
            if self.nulls_last:
                template = "%s NULLS LAST" % template
            elif self.nulls_first:
                template = "%s NULLS FIRST" % template
        else:
            if self.nulls_last and not (
                self.descending and connection.features.order_by_nulls_first
            ):
                template = "%%(expression)s IS NULL, %s" % template
            elif self.nulls_first and not (
                not self.descending and connection.features.order_by_nulls_first
            ):
                template = "%%(expression)s IS NOT NULL, %s" % template
        connection.ops.check_expression_support(self)
        expression_sql, params = compiler.compile(self.expression)
        placeholders = {
            "expression": expression_sql,
            "ordering": "DESC" if self.descending else "ASC",
            **extra_context,
        }
        params *= template.count("%(expression)s")
        return (template % placeholders).rstrip(), params
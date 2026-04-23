def as_sql(self, compiler, connection, template=None, **extra_context):
        connection.ops.check_expression_support(self)
        template_params = {**self.extra, **extra_context}
        subquery_sql, sql_params = self.query.as_sql(compiler, connection)
        template_params["subquery"] = subquery_sql[1:-1]

        template = template or template_params.get("template", self.template)
        sql = template % template_params
        return sql, sql_params
def resolve_expression_parameter(self, compiler, connection, sql, param):
        params = [param]
        if hasattr(param, "resolve_expression"):
            param = param.resolve_expression(compiler.query)
        if hasattr(param, "as_sql"):
            sql, params = compiler.compile(param)
        return sql, params
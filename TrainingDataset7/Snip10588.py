def as_mysql(self, compiler, connection, **extra_context):
        extra_context["function"] = "GROUP_CONCAT"

        template = "%(function)s(%(distinct)s%(expressions)s%(order_by)s%(delimiter)s)"
        extra_context["template"] = template

        c = self.copy()
        # The creation of the delimiter SQL and the ordering of the parameters
        # must be handled explicitly, as MySQL puts the delimiter at the end of
        # the aggregate using the `SEPARATOR` declaration (rather than treating
        # as an expression like other database backends).
        delimiter_params = []
        if c.delimiter:
            delimiter_sql, delimiter_params = compiler.compile(c.delimiter)
            # Drop the delimiter from the source expressions.
            c.source_expressions = c.source_expressions[:-1]
            extra_context["delimiter"] = delimiter_sql

        sql, params = c.as_sql(compiler, connection, **extra_context)

        return sql, (*params, *delimiter_params)
def as_sql(self, compiler, connection, function=None, template=None):
        options_sql = ""
        options_params = ()
        if self.options:
            options_params = (
                ", ".join(
                    connection.ops.compose_sql(f"{option}=%s", [value])
                    for option, value in self.options.items()
                ),
            )
            options_sql = ", %s"
        sql, params = super().as_sql(
            compiler,
            connection,
            function=function,
            template=template,
            options=options_sql,
        )
        return sql, params + options_params
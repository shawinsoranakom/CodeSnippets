def as_sql(self, compiler, connection, function=None, template=None):
        clone = self.copy()
        clone.set_source_expressions(
            [
                Coalesce(
                    (
                        expression
                        if isinstance(expression.output_field, (CharField, TextField))
                        else Cast(expression, TextField())
                    ),
                    Value(""),
                )
                for expression in clone.get_source_expressions()
            ]
        )
        config_sql = None
        config_params = []
        if template is None:
            if clone.config:
                config_sql, config_params = compiler.compile(clone.config)
                template = "%(function)s(%(config)s, %(expressions)s)"
            else:
                template = clone.template
        sql, params = super(SearchVector, clone).as_sql(
            compiler,
            connection,
            function=function,
            template=template,
            config=config_sql,
        )
        extra_params = []
        if clone.weight:
            weight_sql, extra_params = compiler.compile(clone.weight)
            sql = "setweight({}, {})".format(sql, weight_sql)

        return sql, (*config_params, *params, *extra_params)
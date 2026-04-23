def as_postgresql(self, compiler, connection, **extra_context):
        c = self.copy()
        c.set_source_expressions(
            [
                (
                    expression
                    if isinstance(expression.output_field, (CharField, TextField))
                    else Cast(expression, TextField())
                )
                for expression in c.get_source_expressions()
            ]
        )
        return c.pipes_concat_sql(compiler, connection, **extra_context)
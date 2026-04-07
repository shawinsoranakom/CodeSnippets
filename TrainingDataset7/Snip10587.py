def as_oracle(self, compiler, connection, **extra_context):
        if self.order_by:
            template = (
                "%(function)s(%(distinct)s%(expressions)s) WITHIN GROUP (%(order_by)s)"
                "%(filter)s"
            )
        else:
            template = "%(function)s(%(distinct)s%(expressions)s)%(filter)s"

        return self.as_sql(
            compiler,
            connection,
            function="LISTAGG",
            template=template,
            **extra_context,
        )
def pipes_concat_sql(self, compiler, connection, **extra_context):
        coalesced = self.coalesce()
        return super(ConcatPair, coalesced).as_sql(
            compiler,
            connection,
            template="(%(expressions)s)",
            arg_joiner=" || ",
            **extra_context,
        )
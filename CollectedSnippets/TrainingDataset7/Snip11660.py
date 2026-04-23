def as_oracle(self, compiler, connection, **extra_context):
        # Oracle prohibits mixing TextField, JSONField (NCLOB) and CharField
        # (NVARCHAR2), so convert all fields to NCLOB when that type is
        # expected.
        if self.output_field.get_internal_type() in ("TextField", "JSONField"):
            clone = self.copy()
            clone.set_source_expressions(
                [
                    Func(expression, function="TO_NCLOB")
                    for expression in self.get_source_expressions()
                ]
            )
            return super(Coalesce, clone).as_sql(compiler, connection, **extra_context)
        return self.as_sql(compiler, connection, **extra_context)
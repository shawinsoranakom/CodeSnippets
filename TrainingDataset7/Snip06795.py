def as_oracle(self, compiler, connection, **extra_context):
        source_expressions = self.get_source_expressions()
        clone = self.copy()
        clone.set_source_expressions(source_expressions[:1])
        return super(AsGeoJSON, clone).as_sql(compiler, connection, **extra_context)
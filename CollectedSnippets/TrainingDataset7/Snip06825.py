def as_sqlite(self, compiler, connection, **extra_context):
        clone = self.copy()
        if len(self.source_expressions) < 4:
            # Always provide the z parameter for ST_Translate
            clone.source_expressions.append(Value(0))
        return super(Translate, clone).as_sqlite(compiler, connection, **extra_context)
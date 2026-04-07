def as_mysql(self, compiler, connection, **extra_context):
        clone = self.copy()
        # If no precision is provided, set it to the maximum.
        if len(clone.source_expressions) < 2:
            clone.source_expressions.append(Value(100))
        return clone.as_sql(compiler, connection, **extra_context)
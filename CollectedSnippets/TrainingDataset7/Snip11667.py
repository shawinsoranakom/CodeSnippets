def as_oracle(self, compiler, connection, **extra_context):
        expression1 = self.get_source_expressions()[0]
        if isinstance(expression1, Value) and expression1.value is None:
            raise ValueError("Oracle does not allow Value(None) for expression1.")
        return super().as_sql(compiler, connection, **extra_context)
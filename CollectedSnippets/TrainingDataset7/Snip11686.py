def as_oracle(self, compiler, connection, **extra_context):
        return self.as_native(compiler, connection, returning="CLOB", **extra_context)
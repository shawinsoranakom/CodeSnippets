def as_oracle(self, compiler, connection, **extra_context):
        return self.get_substr().as_oracle(compiler, connection, **extra_context)
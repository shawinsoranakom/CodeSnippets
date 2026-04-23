def as_oracle(self, compiler, connection, **extra_context):
        raise NotSupportedError("SHA224 is not supported on Oracle.")
def as_oracle(self, compiler, connection, **extra_context):
        if not connection.features.supports_uuid4_function:
            raise NotSupportedError(
                "UUID4 requires Oracle version 23ai/26ai (23.9) or later."
            )
        return self.as_sql(compiler, connection, function="UUID", **extra_context)
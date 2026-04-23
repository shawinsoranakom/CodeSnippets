def as_sql(self, compiler, connection, **extra_context):
        if not connection.features.supports_uuid7_function:
            raise NotSupportedError("UUID7 is not supported on this database backend.")

        if len(self.source_expressions) == 1:
            if not connection.features.supports_uuid7_function_shift:
                msg = (
                    "The shift argument to UUID7 is not supported "
                    "on this database backend."
                )
                raise NotSupportedError(msg)

        return super().as_sql(compiler, connection, **extra_context)
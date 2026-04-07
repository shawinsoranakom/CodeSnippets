def as_sqlite(self, compiler, connection, **extra_context):
        if (
            self.distinct
            and isinstance(self.delimiter.value, Value)
            and self.delimiter.value.value == ","
        ):
            clone = self.copy()
            source_expressions = clone.get_source_expressions()
            clone.set_source_expressions(
                source_expressions[:1] + source_expressions[2:]
            )

            return clone.as_sql(
                compiler,
                connection,
                function="GROUP_CONCAT",
                **extra_context,
            )

        if connection.get_database_version() < (3, 44):
            return self.as_sql(
                compiler,
                connection,
                function="GROUP_CONCAT",
                **extra_context,
            )

        return self.as_sql(compiler, connection, **extra_context)
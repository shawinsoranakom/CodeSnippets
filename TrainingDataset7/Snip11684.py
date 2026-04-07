def as_native(self, compiler, connection, *, returning, **extra_context):
        # PostgreSQL 16+ and Oracle remove SQL NULL values from the array by
        # default. Adds the NULL ON NULL clause to keep NULL values in the
        # array, mapping them to JSON null values, which matches the behavior
        # of SQLite.
        null_on_null = "NULL ON NULL" if len(self.get_source_expressions()) > 0 else ""

        return self.as_sql(
            compiler,
            connection,
            template=(
                f"%(function)s(%(expressions)s {null_on_null} RETURNING {returning})"
            ),
            **extra_context,
        )
def as_oracle(self, compiler, connection, **extra_context):
        tolerance = Value(
            self._handle_param(
                self.extra.get("tolerance", self.tolerance),
                "tolerance",
                NUMERIC_TYPES,
            )
        )
        clone = self.copy()
        clone.set_source_expressions([*self.get_source_expressions(), tolerance])
        return clone.as_sql(compiler, connection, **extra_context)
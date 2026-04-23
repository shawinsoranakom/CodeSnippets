def binary_placeholder_sql(self, value, compiler):
        if value is None:
            return "%s", (None,)
        elif hasattr(value, "as_sql"):
            return compiler.compile(value)
        return "_binary %s", (value,)
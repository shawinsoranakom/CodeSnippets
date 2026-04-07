def get_placeholder_sql(self, value, compiler, connection):
        if hasattr(value, "as_sql"):
            sql, params = compiler.compile(value)
        else:
            sql, params = "%s", (value,)
        return f"({sql} + %s)", (*params, 1)
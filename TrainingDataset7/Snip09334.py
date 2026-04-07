def binary_placeholder_sql(self, value, compiler):
        """
        Some backends require special syntax to insert binary content (MySQL
        for example uses '_binary %s').
        """
        if hasattr(value, "as_sql"):
            return compiler.compile(value)
        return "%s", (value,)
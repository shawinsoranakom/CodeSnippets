def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        # Distinguish NULL and empty arrays
        return (
            "CASE WHEN %(lhs)s IS NULL THEN NULL ELSE "
            "coalesce(array_length(%(lhs)s, 1), 0) END"
        ) % {"lhs": lhs}, params * 2
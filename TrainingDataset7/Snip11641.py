def as_sql(self, compiler, connection):
        # e.g.: (a, b, c) is None as SQL:
        # WHERE a IS NULL OR b IS NULL OR c IS NULL
        # e.g.: (a, b, c) is not None as SQL:
        # WHERE a IS NOT NULL AND b IS NOT NULL AND c IS NOT NULL
        rhs = self.rhs
        lookups = [IsNull(col, rhs) for col in self.lhs]
        root = WhereNode(lookups, connector=OR if rhs else AND)
        return root.as_sql(compiler, connection)
def process_rhs(self, compiler, connection):
        if not self.rhs_is_direct_value():
            return super(TupleLookupMixin, self).process_rhs(compiler, connection)

        rhs = self.rhs
        if not rhs:
            raise EmptyResultSet

        # e.g.: (a, b, c) in [(x1, y1, z1), (x2, y2, z2)] as SQL:
        # WHERE (a, b, c) IN ((x1, y1, z1), (x2, y2, z2))
        result = []
        lhs = self.lhs

        for vals in rhs:
            # Remove any tuple containing None from the list as NULL is never
            # equal to anything.
            if any(val is None for val in vals):
                continue
            result.append(
                Tuple(
                    *[
                        (
                            val
                            if hasattr(val, "as_sql")
                            else Value(val, output_field=col.output_field)
                        )
                        for col, val in zip(lhs, vals)
                    ]
                )
            )

        if not result:
            raise EmptyResultSet

        return compiler.compile(Tuple(*result))
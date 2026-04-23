def process_rhs(self, compiler, connection):
        if self.rhs_is_direct_value():
            args = [
                (
                    val
                    if hasattr(val, "as_sql")
                    else Value(val, output_field=col.output_field)
                )
                for col, val in zip(self.lhs, self.rhs)
            ]
            return compiler.compile(Tuple(*args))
        else:
            sql, params = compiler.compile(self.rhs)
            if isinstance(self.rhs, ColPairs):
                return "(%s)" % sql, params
            elif isinstance(self.rhs, Query):
                return super().process_rhs(compiler, connection)
            else:
                raise ValueError(
                    "Composite field lookups only work with composite expressions."
                )
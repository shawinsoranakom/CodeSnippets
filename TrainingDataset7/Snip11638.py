def as_sql(self, compiler, connection):
        if (
            not connection.features.supports_tuple_comparison_against_subquery
            and isinstance(self.rhs, Query)
            and self.rhs.subquery
            and isinstance(
                self, (GreaterThan, GreaterThanOrEqual, LessThan, LessThanOrEqual)
            )
        ):
            lookup = self.lookup_name
            msg = (
                f'"{lookup}" cannot be used to target composite fields '
                "through subqueries on this backend"
            )
            raise NotSupportedError(msg)
        if not connection.features.supports_tuple_lookups:
            return self.get_fallback_sql(compiler, connection)
        return super().as_sql(compiler, connection)
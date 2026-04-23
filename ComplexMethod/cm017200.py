def _unique_supported(
        self,
        condition=None,
        deferrable=None,
        include=None,
        expressions=None,
        nulls_distinct=None,
    ):
        return (
            (not condition or self.connection.features.supports_partial_indexes)
            and (
                not deferrable
                or self.connection.features.supports_deferrable_unique_constraints
            )
            and (not include or self.connection.features.supports_covering_indexes)
            and (
                not expressions or self.connection.features.supports_expression_indexes
            )
            and (
                nulls_distinct is None
                or self.connection.features.supports_nulls_distinct_unique_constraints
            )
        )
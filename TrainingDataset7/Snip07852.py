def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        resolved = super().resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )
        if self.config:
            resolved.config = self.config.resolve_expression(
                query, allow_joins, reuse, summarize, for_save
            )
        return resolved
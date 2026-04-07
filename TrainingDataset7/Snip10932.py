def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        c = super().resolve_expression(query, allow_joins, reuse, summarize, for_save)
        if for_save and c.condition is not None:
            # Resolve condition with for_save=False, since it's used as a
            # filter.
            c.condition = self.condition.resolve_expression(
                query, allow_joins, reuse, summarize, for_save=False
            )
        return c
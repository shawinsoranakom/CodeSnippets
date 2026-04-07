def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        c = self.copy()
        c.is_summary = summarize
        c.lhs = self.lhs.resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )
        if hasattr(self.rhs, "resolve_expression"):
            c.rhs = self.rhs.resolve_expression(
                query, allow_joins, reuse, summarize, for_save
            )
        return c
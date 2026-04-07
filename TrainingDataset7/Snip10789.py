def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        """
        Provide the chance to do any preprocessing or validation before being
        added to the query.

        Arguments:
         * query: the backend query implementation
         * allow_joins: boolean allowing or denying use of joins
           in this query
         * reuse: a set of reusable joins for multijoins
         * summarize: a terminal aggregate clause
         * for_save: whether this expression about to be used in a save or
           update

        Return: an Expression to be added to the query.
        """
        c = self.copy()
        c.is_summary = summarize
        source_expressions = [
            (
                expr.resolve_expression(query, allow_joins, reuse, summarize, for_save)
                if expr is not None
                else None
            )
            for expr in c.get_source_expressions()
        ]
        if not self.allows_composite_expressions and any(
            isinstance(expr, ColPairs) for expr in source_expressions
        ):
            raise ValueError(
                f"{self.__class__.__name__} expression does not support "
                "composite primary keys."
            )
        c.set_source_expressions(source_expressions)
        return c
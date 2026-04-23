def resolve_expression(
        self,
        query=None,
        allow_joins=True,
        reuse=None,
        summarize=False,
        for_save=False,
    ):
        resolved = query.resolve_ref(self.name, allow_joins, reuse, summarize)
        if isinstance(self.obj, (OuterRef, self.__class__)):
            expr = self.obj.resolve_expression(
                query, allow_joins, reuse, summarize, for_save
            )
        else:
            expr = resolved
        return resolved.output_field.slice_expression(expr, self.start, self.length)
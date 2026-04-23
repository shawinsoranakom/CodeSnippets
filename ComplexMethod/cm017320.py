def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        # Aggregates are not allowed in UPDATE queries, so ignore for_save
        c = super().resolve_expression(query, allow_joins, reuse, summarize)
        if summarize:
            # Summarized aggregates cannot refer to summarized aggregates.
            for ref in c.get_refs():
                if query.annotations[ref].is_summary:
                    raise FieldError(
                        f"Cannot compute {c.name}('{ref}'): '{ref}' is an aggregate"
                    )
        elif not self.is_summary:
            # Call Aggregate.get_source_expressions() to avoid
            # returning self.filter and including that in this loop.
            expressions = super(Aggregate, c).get_source_expressions()
            for index, expr in enumerate(expressions):
                if expr.contains_aggregate:
                    before_resolved = self.get_source_expressions()[index]
                    name = (
                        before_resolved.name
                        if hasattr(before_resolved, "name")
                        else repr(before_resolved)
                    )
                    raise FieldError(
                        "Cannot compute %s('%s'): '%s' is an aggregate"
                        % (c.name, name, name)
                    )
        if (default := c.default) is None:
            return c
        if hasattr(default, "resolve_expression"):
            default = default.resolve_expression(query, allow_joins, reuse, summarize)
            if default._output_field_or_none is None:
                default.output_field = c._output_field_or_none
        else:
            default = Value(default, c._output_field_or_none)
        c.default = None  # Reset the default argument before wrapping.
        coalesce = Coalesce(c, default, output_field=c._output_field_or_none)
        coalesce.is_summary = c.is_summary
        return coalesce
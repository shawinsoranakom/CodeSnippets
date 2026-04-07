def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        resolved_expression = self.expression.resolve_expression(
            query=query,
            allow_joins=allow_joins,
            reuse=reuse,
            summarize=summarize,
            for_save=for_save,
        )
        # Defaults used outside an INSERT context should resolve to their
        # underlying expression.
        if not for_save:
            return resolved_expression
        return DatabaseDefault(
            resolved_expression, output_field=self._output_field_or_none
        )
def referenced_fields(self):
        resolved_expression = self.expression.resolve_expression(
            self._query, allow_joins=False
        )
        referenced_fields = []
        for col in self._query._gen_cols([resolved_expression]):
            referenced_fields.append(col.target)
        return frozenset(referenced_fields)
def get_combinator_sql(self, combinator, all):
        features = self.connection.features
        compilers = [
            query.get_compiler(self.using, self.connection, self.elide_empty)
            for query in self.query.combined_queries
        ]
        if not features.supports_slicing_ordering_in_compound:
            for compiler in compilers:
                if compiler.query.is_sliced:
                    raise DatabaseError(
                        "LIMIT/OFFSET not allowed in subqueries of compound statements."
                    )
                if compiler.get_order_by():
                    raise DatabaseError(
                        "ORDER BY not allowed in subqueries of compound statements."
                    )
        parts = []
        empty_compiler = None
        for compiler in compilers:
            try:
                parts.append(self._get_combinator_part_sql(compiler))
            except EmptyResultSet:
                # Omit the empty queryset with UNION and with DIFFERENCE if the
                # first queryset is nonempty.
                if combinator == "union" or (combinator == "difference" and parts):
                    empty_compiler = compiler
                    continue
                raise
        if not parts:
            raise EmptyResultSet
        elif len(parts) == 1 and combinator == "union" and self.query.is_sliced:
            # A sliced union cannot be composed of a single component because
            # in the event the later is also sliced it might result in invalid
            # SQL due to the usage of multiple LIMIT clauses. Prevent that from
            # happening by always including an empty resultset query to force
            # the creation of an union.
            empty_compiler.elide_empty = False
            parts.append(self._get_combinator_part_sql(empty_compiler))
        combinator_sql = self.connection.ops.set_operators[combinator]
        if all and combinator == "union":
            combinator_sql += " ALL"
        braces = "{}"
        if not self.query.subquery and features.supports_slicing_ordering_in_compound:
            braces = "({})"
        sql_parts, args_parts = zip(
            *((braces.format(sql), args) for sql, args in parts)
        )
        result = [" {} ".format(combinator_sql).join(sql_parts)]
        params = []
        for part in args_parts:
            params.extend(part)
        return result, params
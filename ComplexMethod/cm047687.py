def subselect(self, *args: str | SQL) -> SQL:
        """ Similar to :meth:`.select`, but for sub-queries.
            This one avoids the ORDER BY clause when possible,
            and includes parentheses around the subquery.
        """
        if self._ids is not None and not args:
            # inject the known result instead of the subquery
            if not self._ids:
                # in case we have nothing, we want to use a sub_query with no records
                # because an empty tuple leads to a syntax error
                # and a tuple containing just None creates issues for `NOT IN`
                return SQL("(SELECT 1 WHERE FALSE)")
            return SQL("%s", self._ids)

        if self.limit or self.offset:
            # in this case, the ORDER BY clause is necessary
            return SQL("(%s)", self.select(*args))

        sql_args = map(SQL, args) if args else [SQL.identifier(self.table, 'id')]
        return SQL(
            "(%s%s%s)",
            SQL("SELECT %s", SQL(", ").join(sql_args)),
            SQL(" FROM %s", self.from_clause),
            SQL(" WHERE %s", self.where_clause) if self._where_clauses else SQL(),
        )
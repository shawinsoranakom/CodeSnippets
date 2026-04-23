def select(self, *args: str | SQL) -> SQL:
        """ Return the SELECT query as an ``SQL`` object. """
        sql_args = map(SQL, args) if args else [SQL.identifier(self.table, 'id')]
        return SQL(
            "%s%s%s%s%s%s%s%s",
            SQL("SELECT %s", SQL(", ").join(sql_args)),
            SQL(" FROM %s", self.from_clause),
            SQL(" WHERE %s", self.where_clause) if self._where_clauses else SQL(),
            SQL(" GROUP BY %s", self.groupby) if self.groupby else SQL(),
            SQL(" HAVING %s", self.having) if self.having else SQL(),
            SQL(" ORDER BY %s", self._order) if self._order else SQL(),
            SQL(" LIMIT %s", self.limit) if self.limit else SQL(),
            SQL(" OFFSET %s", self.offset) if self.offset else SQL(),
        )
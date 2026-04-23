def add_join(self, kind: str, alias: str, table: str | SQL | None, condition: SQL):
        """ Add a join clause with the given alias, table and condition. """
        sql_kind = _SQL_JOINS.get(kind.upper())
        assert sql_kind is not None, f"Invalid JOIN type {kind!r}"
        assert alias not in self._tables, f"Alias {alias!r} already used"
        table = table or alias
        if isinstance(table, str):
            table = SQL.identifier(table)

        if alias in self._joins:
            assert self._joins[alias] == (sql_kind, table, condition)
        else:
            self._joins[alias] = (sql_kind, table, condition)
            self._ids = self._ids and None
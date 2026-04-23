def try_lock_for_update(self, *, allow_referencing: bool = False, limit: int | None = None) -> Self:
        """ Grab an exclusive write-lock on some rows with the given ids.

        Skip locked records and browse the records that could be locked.

        :param allow_referencing: Acquire a row lock which allows for other
            transactions to reference this record. Use only when modifying
            values that are not identifiers.
        :param limit: The maximum number of rows to lock
        :return: The recordset of locked records
        """
        new_ids, ids = partition(lambda i: isinstance(i, NewId), self._ids)
        if limit is not None:
            if len(new_ids) >= limit:
                return self.browse(new_ids[:limit])
            # keep the order of ids when trying to lock
            query = self.browse(ids)._as_query(ordered=True)
            query.limit = limit - len(new_ids)
        else:
            query = Query(self.env, self._table, self._table_sql)
            query.add_where(SQL("%s IN %s", SQL.identifier(self._table, 'id'), tuple(ids)))
        if not ids:
            return self
        if allow_referencing:
            lock_sql = SQL("FOR NO KEY UPDATE SKIP LOCKED")
        else:
            lock_sql = SQL("FOR UPDATE SKIP LOCKED")
        sql = SQL("%s %s", query.select(), lock_sql)
        real_ids = (id_ for [id_] in self.env.execute_query(sql))
        valid_ids = {*real_ids, *new_ids}
        return self.browse(i for i in self._ids if i in valid_ids)
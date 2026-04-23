def _parent_store_update_prepare(self, vals_list: list[ValuesType]) -> Self:
        """ Return the records in ``self`` that must update their parent_path
            field. This must be called before updating the parent field.
        """
        if not self._parent_store:
            return self.browse()

        # associate each new parent_id to its corresponding record ids
        parent_to_ids = defaultdict(list)
        for id_, vals in zip(self._ids, vals_list):
            if self._parent_name in vals:
                parent_to_ids[vals[self._parent_name]].append(id_)

        if not parent_to_ids:
            return self.browse()

        self.flush_recordset([self._parent_name])

        # return the records for which the parent field will change
        sql_parent = SQL.identifier(self._parent_name)
        conditions = []
        for parent_id, ids in parent_to_ids.items():
            if parent_id:
                condition = SQL('(%s != %s OR %s IS NULL)', sql_parent, parent_id, sql_parent)
            else:
                condition = SQL('%s IS NOT NULL', sql_parent)
            conditions.append(SQL('("id" IN %s AND %s)', tuple(ids), condition))

        rows = self.env.execute_query(SQL(
            "SELECT id FROM %s WHERE %s ORDER BY id",
            SQL.identifier(self._table),
            SQL(" OR ").join(conditions),
        ))
        return self.browse(row[0] for row in rows)
def _update(self, values, returning_fields=None):
        """
        A version of update() that accepts field objects instead of field
        names. Used primarily for model saving and not intended for use by
        general code (it requires too much poking around at model internals to
        be useful at that level).
        """
        if self.query.is_sliced:
            raise TypeError("Cannot update a query once a slice has been taken.")
        query = self.query.chain(sql.UpdateQuery)
        query.add_update_fields(values)
        # Clear any annotations so that they won't be present in subqueries.
        query.annotations = {}
        self._result_cache = None
        if returning_fields is None:
            return query.get_compiler(self.db).execute_sql(ROW_COUNT)
        return query.get_compiler(self.db).execute_returning_sql(returning_fields)
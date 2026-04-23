def _check_removed_columns(self, log=False):
        if self._abstract:
            return
        # iterate on the database columns to drop the NOT NULL constraints of
        # fields which were required but have been removed (or will be added by
        # another module)
        cr = self.env.cr
        cols = [name for name, field in self._fields.items()
                     if field.store and field.column_type]
        cr.execute(SQL(
            """ SELECT a.attname, a.attnotnull
                  FROM pg_class c, pg_attribute a
                 WHERE c.relname=%s
                   AND c.relnamespace = current_schema::regnamespace
                   AND c.oid=a.attrelid
                   AND a.attisdropped=%s
                   AND pg_catalog.format_type(a.atttypid, a.atttypmod) NOT IN ('cid', 'tid', 'oid', 'xid')
                   AND a.attname NOT IN %s """,
            self._table, False, tuple(cols),
        ))

        for row in cr.dictfetchall():
            if log:
                _logger.debug("column %s is in the table %s but not in the corresponding object %s",
                              row['attname'], self._table, self._name)
            if row['attnotnull']:
                sql.drop_not_null(cr, self._table, row['attname'])
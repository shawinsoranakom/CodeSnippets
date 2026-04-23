def _write_multi(self, vals_list: list[ValuesType]) -> None:
        """ Low-level implementation of write() """
        assert len(self) == len(vals_list)

        if not self:
            return

        # determine records that require updating parent_path
        parent_records = self._parent_store_update_prepare(vals_list)

        if self._log_access:
            # set magic fields (already done by write(), but not for computed fields)
            log_vals = {'write_uid': self.env.uid, 'write_date': self.env.cr.now()}
            vals_list = [(log_vals | vals) for vals in vals_list]

        # determine SQL updates, grouped by set of updated fields:
        # {(col1, col2, col3): [(id, val1, val2, val3)]}
        updates = defaultdict(list)
        for record, vals in zip(self, vals_list):
            # sort vals.items() by key, then retrieve its keys and values
            fnames, row = zip(*sorted(vals.items()))
            updates[fnames].append(record._ids + row)

        # perform updates (fnames, rows) in batches
        updates_list = [
            (fnames, sub_rows)
            for fnames, rows in updates.items()
            for sub_rows in split_every(UPDATE_BATCH_SIZE, rows)
        ]

        # update columns by group of updated fields
        for fnames, rows in updates_list:
            columns = []
            assignments = []
            for fname in fnames:
                field = self._fields[fname]
                assert field.store and field.column_type
                column = SQL.identifier(fname)
                # the type cast is necessary for some values, like NULLs
                expr = SQL('"__tmp".%s::%s', column, SQL(field.column_type[1]))
                if field.translate is True:
                    # this is the SQL equivalent of:
                    # None if expr is None else (
                    #     (column or {'en_US': next(iter(expr.values()))}) | expr
                    # )
                    expr = SQL(
                        """CASE WHEN %(expr)s IS NULL THEN NULL ELSE
                            COALESCE(%(table)s.%(column)s, jsonb_build_object(
                                'en_US', jsonb_path_query_first(%(expr)s, '$.*')
                            )) || %(expr)s
                        END""",
                        table=SQL.identifier(self._table),
                        column=column,
                        expr=expr,
                    )
                if field.company_dependent:
                    fallbacks = self.env['ir.default']._get_field_column_fallbacks(self._name, fname)
                    expr = SQL(
                        """(SELECT jsonb_object_agg(d.key, d.value)
                        FROM jsonb_each(COALESCE(%(table)s.%(column)s, '{}'::jsonb) || %(expr)s) d
                        JOIN jsonb_each(%(fallbacks)s) f
                        ON d.key = f.key AND d.value != f.value)""",
                        table=SQL.identifier(self._table),
                        column=column,
                        expr=expr,
                        fallbacks=fallbacks
                    )
                columns.append(column)
                assignments.append(SQL("%s = %s", column, expr))

            self.env.execute_query(SQL(
                """ UPDATE %(table)s
                    SET %(assignments)s
                    FROM (VALUES %(values)s) AS "__tmp"("id", %(columns)s)
                    WHERE %(table)s."id" = "__tmp"."id"
                """,
                table=SQL.identifier(self._table),
                assignments=SQL(", ").join(assignments),
                values=SQL(", ").join(rows),
                columns=SQL(", ").join(columns),
            ))

        # update parent_path
        if parent_records:
            parent_records._parent_store_update()
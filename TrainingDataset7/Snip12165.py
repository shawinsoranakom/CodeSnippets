def execute_sql(self, returning_fields=None):
        assert not (
            returning_fields
            and len(self.query.objs) != 1
            and not self.connection.features.can_return_rows_from_bulk_insert
        )
        opts = self.query.get_meta()
        self.returning_fields = returning_fields
        cols = []
        with self.connection.cursor() as cursor:
            for sql, params in self.as_sql():
                cursor.execute(sql, params)
            if not self.returning_fields:
                return []
            obj_len = len(self.query.objs)
            if (
                self.connection.features.can_return_rows_from_bulk_insert
                and obj_len > 1
            ) or (
                self.connection.features.can_return_columns_from_insert and obj_len == 1
            ):
                rows = self.connection.ops.fetch_returned_rows(
                    cursor, self.returning_params
                )
                cols = [field.get_col(opts.db_table) for field in self.returning_fields]
            elif returning_fields and isinstance(
                returning_field := returning_fields[0], AutoField
            ):
                cols = [returning_field.get_col(opts.db_table)]
                rows = [
                    (
                        self.connection.ops.last_insert_id(
                            cursor,
                            opts.db_table,
                            returning_field.column,
                        ),
                    )
                ]
            else:
                # Backend doesn't support returning fields and no auto-field
                # that can be retrieved from `last_insert_id` was specified.
                return []
        converters = self.get_converters(cols)
        if converters:
            rows = self.apply_converters(rows, converters)
        return list(rows)
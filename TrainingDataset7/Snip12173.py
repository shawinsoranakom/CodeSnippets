def execute_returning_sql(self, returning_fields):
        """
        Execute the specified update and return rows of the returned columns
        associated with the specified returning_field if the backend supports
        it.
        """
        if self.query.get_related_updates():
            raise NotImplementedError(
                "Update returning is not implemented for queries with related updates."
            )

        if (
            not returning_fields
            or not self.connection.features.can_return_rows_from_update
        ):
            row_count = self.execute_sql(ROW_COUNT)
            return [()] * row_count

        self.returning_fields = returning_fields
        with self.connection.cursor() as cursor:
            sql, params = self.as_sql()
            cursor.execute(sql, params)
            rows = self.connection.ops.fetch_returned_rows(
                cursor, self.returning_params
            )
        opts = self.query.get_meta()
        cols = [field.get_col(opts.db_table) for field in self.returning_fields]
        converters = self.get_converters(cols)
        if converters:
            rows = self.apply_converters(rows, converters)
        return list(rows)
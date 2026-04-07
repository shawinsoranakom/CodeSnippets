def returning_columns(self, fields):
        """
        For backends that support returning columns as part of an insert or
        update query, return the SQL and params to append to the query.
        The returned fragment should contain a format string to hold the
        appropriate column.
        """
        if not fields:
            return "", ()
        columns = [
            "%s.%s"
            % (
                self.quote_name(field.model._meta.db_table),
                self.quote_name(field.column),
            )
            for field in fields
        ]
        return "RETURNING %s" % ", ".join(columns), ()
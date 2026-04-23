def _get_column_allows_null(self, table, column, using):
        return [
            c.null_ok
            for c in self.get_table_description(table, using=using)
            if c.name == column
        ][0]
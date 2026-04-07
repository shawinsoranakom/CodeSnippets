def _get_column_collation(self, table, column, using):
        return next(
            f.collation
            for f in self.get_table_description(table, using=using)
            if f.name == column
        )
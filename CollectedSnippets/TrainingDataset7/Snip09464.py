def rename_column_references(self, table, old_column, new_column):
        super().rename_column_references(table, old_column, new_column)
        self.to_reference.rename_column_references(table, old_column, new_column)
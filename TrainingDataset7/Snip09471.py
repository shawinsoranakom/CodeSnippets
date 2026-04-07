def rename_column_references(self, table, old_column, new_column):
        for part in self.parts.values():
            if hasattr(part, "rename_column_references"):
                part.rename_column_references(table, old_column, new_column)
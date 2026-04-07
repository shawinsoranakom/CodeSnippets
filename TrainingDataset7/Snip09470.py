def rename_table_references(self, old_table, new_table):
        for part in self.parts.values():
            if hasattr(part, "rename_table_references"):
                part.rename_table_references(old_table, new_table)
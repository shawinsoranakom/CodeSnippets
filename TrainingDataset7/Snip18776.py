def rename_table_references(self, old_table, new_table):
        if old_table in self.referenced_tables:
            self.referenced_tables.remove(old_table)
            self.referenced_tables.add(new_table)
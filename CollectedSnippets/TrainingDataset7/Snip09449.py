def rename_table_references(self, old_table, new_table):
        if self.table == old_table:
            self.table = new_table
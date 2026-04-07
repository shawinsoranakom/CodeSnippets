def assertColumnExists(self, table, column):
        self.assertIn(column, [c.name for c in self.get_table_description(table)])
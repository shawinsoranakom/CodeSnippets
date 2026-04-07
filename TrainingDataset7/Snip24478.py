def assertColumnNotExists(self, table, column):
        self.assertNotIn(column, [c.name for c in self.get_table_description(table)])
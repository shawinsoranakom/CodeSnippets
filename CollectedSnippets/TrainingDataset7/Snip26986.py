def assertColumnExists(self, table, column, using="default"):
        self.assertIn(
            column, [c.name for c in self.get_table_description(table, using=using)]
        )
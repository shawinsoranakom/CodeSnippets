def assertColumnNotExists(self, table, column, using="default"):
        self.assertNotIn(
            column, [c.name for c in self.get_table_description(table, using=using)]
        )
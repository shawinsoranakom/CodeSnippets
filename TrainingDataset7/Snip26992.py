def assertColumnCollation(self, table, column, collation, using="default"):
        self.assertEqual(self._get_column_collation(table, column, using), collation)
def assertColumnNull(self, table, column, using="default"):
        self.assertTrue(self._get_column_allows_null(table, column, using))
def assertColumnNotNull(self, table, column, using="default"):
        self.assertFalse(self._get_column_allows_null(table, column, using))
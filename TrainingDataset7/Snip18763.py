def test_repr(self):
        self.assertEqual(
            repr(self.reference),
            "<IndexName 'table_first_column_suffix, table_second_column_suffix'>",
        )
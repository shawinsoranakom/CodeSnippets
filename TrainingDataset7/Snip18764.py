def test_str(self):
        self.assertEqual(
            str(self.reference), "table_first_column_suffix, table_second_column_suffix"
        )
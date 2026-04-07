def test_str(self):
        self.assertEqual(
            str(self.reference),
            "table_first_column_to_table_to_first_column_fk, "
            "table_second_column_to_table_to_first_column_fk",
        )
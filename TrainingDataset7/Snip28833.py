def test_tablespace_ignored_for_model(self):
        # No tablespace-related SQL
        self.assertEqual(sql_for_table(Scientist), sql_for_table(ScientistRef))
def test_sequence_reset_by_name_sql(self):
        self.assertEqual(self.ops.sequence_reset_by_name_sql(None, []), [])
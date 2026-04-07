def test_deferrable_sql(self):
        self.assertEqual(self.ops.deferrable_sql(), "")
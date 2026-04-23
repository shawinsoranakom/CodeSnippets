def test_tablespace_sql(self):
        self.assertEqual(self.ops.tablespace_sql(None), "")
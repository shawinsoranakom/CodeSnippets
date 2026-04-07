def test_sql_flush_no_tables(self):
        self.assertEqual(connection.ops.sql_flush(no_style(), []), [])
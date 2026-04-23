def assertSQLFormatted(self, handler, sql, total_calls=1):
        self.assertEqual(len(self.format_sql_calls), total_calls)
        formatted_sql = self.format_sql_calls[0][sql]
        expected = f"=> Executing query duration=3.142 sql={formatted_sql}"
        self.assertLogRecord(handler, expected)
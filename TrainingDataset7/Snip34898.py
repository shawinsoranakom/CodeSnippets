def test_formats_sql_multiple_non_matching_sql(self):
        handler = self.make_handler()
        msg = "=> Executing query duration=%.3f sql=%s"
        sql1 = "select * from foo"
        sql2 = "select * from other"

        self.do_log(msg, 3.1416, sql1, extra={"duration": 3.1416, "sql": sql2})
        self.assertSQLFormatted(handler, sql1, total_calls=2)
        # Second format call is triggered since the sql are different.
        self.assertEqual(list(self.format_sql_calls[1].keys()), [sql2])
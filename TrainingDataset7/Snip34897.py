def test_formats_sql_multiple_matching_sql(self):
        handler = self.make_handler()
        msg = "=> Executing query duration=%.3f sql=%s"
        sql = "select * from foo"

        self.do_log(msg, 3.1416, sql, extra={"duration": 3.1416, "sql": sql})
        self.assertSQLFormatted(handler, sql)
def test_formats_sql_default_percent_format_style(self):
        handler = self.make_handler()
        msg = "=> Executing query duration=%.3f sql=%s"
        sql = "select * from foo"

        self.do_log(msg, 3.1416, sql)
        self.assertSQLFormatted(handler, sql)
def test_formats_sql_named_percent_format_style(self):
        handler = self.make_handler()
        msg = "=> Executing query duration=%(duration).3f sql=%(sql)s"
        sql = "select * from foo"

        self.do_log(msg, {"duration": 3.1416, "sql": sql})
        self.assertSQLFormatted(handler, sql)
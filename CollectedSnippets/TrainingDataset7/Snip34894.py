def test_formats_sql_named_fmt_format_style(self):
        handler = self.make_handler(
            fmt="%(message)s duration=%(duration).3f sql=%(sql)s"
        )
        msg = "=> Executing query"
        sql = "select * from foo"

        self.do_log(msg, extra={"sql": sql, "duration": 3.1416})
        self.assertSQLFormatted(handler, sql)
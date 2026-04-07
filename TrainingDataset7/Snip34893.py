def test_formats_sql_bracket_format_style(self):
        handler = self.make_handler(
            fmt="{message} duration={duration:.3f} sql={sql}", style="{"
        )
        msg = "=> Executing query"
        sql = "select * from foo"

        self.do_log(msg, extra={"sql": sql, "duration": 3.1416})
        self.assertSQLFormatted(handler, sql)
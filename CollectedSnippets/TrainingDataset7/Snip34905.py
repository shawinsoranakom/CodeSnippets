def test_log_record_sql_extra_none(self):
        handler = self.make_handler(
            fmt="{message} duration={duration:.3f} sql={sql}", style="{"
        )
        msg = "=> Executing query"

        self.do_log(msg, extra={"sql": None, "duration": 3.1416})
        self.assertEqual(self.format_sql_calls, [])
        self.assertLogRecord(handler, f"{msg} duration=3.142 sql=None")
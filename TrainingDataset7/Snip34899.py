def test_log_record_no_args(self):
        handler = self.make_handler()
        msg = "=> Executing query no args"

        self.do_log(msg)
        self.assertEqual(self.format_sql_calls, [])
        self.assertLogRecord(handler, msg)
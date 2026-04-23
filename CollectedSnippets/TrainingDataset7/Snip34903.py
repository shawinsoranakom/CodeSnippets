def test_log_record_sql_arg_none(self):
        handler = self.make_handler()
        msg = "=> Executing query duration=%.3f sql=%s"
        args = (3.1416, None)

        self.do_log(msg, *args)
        self.assertEqual(self.format_sql_calls, [])
        self.assertLogRecord(handler, msg % args)
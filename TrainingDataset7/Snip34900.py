def test_log_record_not_enough_args(self):
        handler = self.make_handler()
        msg = "=> Executing query one args %r"
        args = "not formatted"

        self.do_log(msg, args)
        self.assertEqual(self.format_sql_calls, [])
        self.assertLogRecord(handler, msg % args)
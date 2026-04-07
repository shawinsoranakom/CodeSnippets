def test_log_record_no_alias(self):
        handler = self.make_handler()
        msg = "=> Executing query duration=%.3f sql=%s"
        args = (3.1416, "select * from foo")

        self.do_log(msg, *args, extra={"alias": "does not exist"})
        self.assertEqual(self.format_sql_calls, [])
        self.assertLogRecord(handler, msg % args)
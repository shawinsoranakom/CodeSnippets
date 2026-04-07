def test_log_record_sql_key_none(self):
        handler = self.make_handler()
        msg = "=> Executing query duration=%(duration).3f sql=%(sql)s"
        args = {"duration": 3.1416, "sql": None}

        self.do_log(msg, args)
        self.assertEqual(self.format_sql_calls, [])
        self.assertLogRecord(handler, msg % args)
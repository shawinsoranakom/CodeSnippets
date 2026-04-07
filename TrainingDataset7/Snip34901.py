def test_log_record_not_key_in_dict_args(self):
        handler = self.make_handler()
        msg = "=> Executing query missing sql key %(foo)r"
        args = {"foo": "bar"}

        self.do_log(msg, args)
        self.assertEqual(self.format_sql_calls, [])
        self.assertLogRecord(handler, msg % args)
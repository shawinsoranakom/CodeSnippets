def test_queries_logger(self):
        sql = "select 1" + connection.features.bare_select_suffix
        with (
            connection.cursor() as cursor,
            self.assertLogs("django.db.backends", "DEBUG") as handler,
        ):
            cursor.execute(sql)
        self.assertGreaterEqual(
            records_len := len(handler.records),
            1,
            f"Wrong number of calls for {handler=} in (expected at least 1, got "
            f"{records_len}).",
        )
        record = handler.records[-1]
        # Log raw message, effective level and args are correct.
        self.assertEqual(record.msg, "(%.3f) %s; args=%s; alias=%s")
        self.assertEqual(record.levelno, logging.DEBUG)
        self.assertEqual(len(record.args), 4)
        duration, logged_sql, params, alias = record.args
        # Duration is hard to test without mocking time, expect under 1 second.
        self.assertIsInstance(duration, float)
        self.assertLess(duration, 1)
        self.assertEqual(duration, record.duration)
        # SQL is correct and not formatted.
        self.assertEqual(logged_sql, sql)
        self.assertNotEqual(logged_sql, connection.ops.format_debug_sql(sql))
        self.assertEqual(logged_sql, record.sql)
        # Params is None and alias is connection.alias.
        self.assertIsNone(params)
        self.assertIsNone(record.params)
        self.assertEqual(alias, connection.alias)
        self.assertEqual(alias, record.alias)
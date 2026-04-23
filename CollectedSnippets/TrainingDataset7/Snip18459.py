def test_no_logs_without_debug(self):
        if isinstance(self._outcome.result, DebugSQLTextTestResult):
            self.skipTest("--debug-sql interferes with this test")
        with self.assertNoLogs("django.db.backends", "DEBUG"):
            with self.assertRaises(Exception), transaction.atomic():
                Person.objects.create(first_name="first", last_name="last")
                raise Exception("Force rollback")

            conn = connections[DEFAULT_DB_ALIAS]
            self.assertEqual(len(conn.queries_log), 0)
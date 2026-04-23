def test_rollback_debug_log(self):
        conn = connections[DEFAULT_DB_ALIAS]
        with CaptureQueriesContext(conn):
            with self.assertLogs("django.db.backends", "DEBUG") as cm:
                with self.assertRaises(Exception), transaction.atomic():
                    Person.objects.create(first_name="first", last_name="last")
                    raise Exception("Force rollback")

                self.assertEqual(conn.queries_log[-1]["sql"], "ROLLBACK")
                self.assertRegex(
                    cm.output[-1],
                    r"DEBUG:django.db.backends:\(\d+.\d{3}\) "
                    rf"ROLLBACK; args=None; alias={DEFAULT_DB_ALIAS}",
                )
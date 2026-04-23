def test_commit_debug_log(self):
        conn = connections[DEFAULT_DB_ALIAS]
        with CaptureQueriesContext(conn):
            with self.assertLogs("django.db.backends", "DEBUG") as cm:
                with transaction.atomic():
                    Person.objects.create(first_name="first", last_name="last")

                self.assertGreaterEqual(len(conn.queries_log), 3)
                self.assertEqual(conn.queries_log[-3]["sql"], "BEGIN")
                self.assertRegex(
                    cm.output[0],
                    r"DEBUG:django.db.backends:\(\d+.\d{3}\) "
                    rf"BEGIN; args=None; alias={DEFAULT_DB_ALIAS}",
                )
                self.assertEqual(conn.queries_log[-1]["sql"], "COMMIT")
                self.assertRegex(
                    cm.output[-1],
                    r"DEBUG:django.db.backends:\(\d+.\d{3}\) "
                    rf"COMMIT; args=None; alias={DEFAULT_DB_ALIAS}",
                )
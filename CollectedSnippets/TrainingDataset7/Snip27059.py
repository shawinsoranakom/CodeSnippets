def test_migrate_syncdb_app_label(self):
        """
        Running migrate --run-syncdb with an app_label only creates tables for
        the specified app.
        """
        stdout = io.StringIO()
        with mock.patch.object(BaseDatabaseSchemaEditor, "execute") as execute:
            call_command(
                "migrate", "unmigrated_app_syncdb", run_syncdb=True, stdout=stdout
            )
            create_table_count = len(
                [call for call in execute.mock_calls if "CREATE TABLE" in str(call)]
            )
            self.assertEqual(create_table_count, 3)
            self.assertGreater(len(execute.mock_calls), 3)
            self.assertIn(
                "Synchronize unmigrated app: unmigrated_app_syncdb", stdout.getvalue()
            )
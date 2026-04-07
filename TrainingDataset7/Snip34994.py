def test_other_only(self):
        self.assertSkippedDatabases(
            ["test_runner_apps.databases.tests.OtherDatabaseTests"], {"other": False}
        )
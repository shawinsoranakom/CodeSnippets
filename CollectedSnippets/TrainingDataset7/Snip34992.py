def test_default_and_other(self):
        self.assertSkippedDatabases(
            [
                "test_runner_apps.databases.tests.DefaultDatabaseTests",
                "test_runner_apps.databases.tests.OtherDatabaseTests",
            ],
            {"default": False, "other": False},
        )
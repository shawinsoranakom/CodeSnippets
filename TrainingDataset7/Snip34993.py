def test_default_only(self):
        self.assertSkippedDatabases(
            [
                "test_runner_apps.databases.tests.DefaultDatabaseTests",
            ],
            {"default": False},
        )
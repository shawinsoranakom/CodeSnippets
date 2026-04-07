def test_no_databases_required(self):
        self.assertSkippedDatabases(
            ["test_runner_apps.databases.tests.NoDatabaseTests"], {}
        )
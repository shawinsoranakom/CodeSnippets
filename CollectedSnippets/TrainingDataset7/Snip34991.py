def test_all(self):
        databases, output = self.get_databases(
            ["test_runner_apps.databases.tests.AllDatabasesTests"]
        )
        self.assertEqual(databases, {alias: False for alias in connections})
        self.assertNotIn(self.skip_msg, output)
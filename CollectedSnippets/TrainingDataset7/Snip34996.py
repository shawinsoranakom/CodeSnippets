def test_serialize(self):
        databases, _ = self.get_databases(
            ["test_runner_apps.databases.tests.DefaultDatabaseSerializedTests"]
        )
        self.assertEqual(databases, {"default": True})
def test_mixed(self):
        databases, output = self.get_databases(["test_runner_apps.databases.tests"])
        self.assertEqual(databases, {"default": True, "other": False})
        self.assertNotIn(self.skip_msg, output)
def test_initialization_display_name(self):
        self.assertEqual(BaseDatabaseWrapper.display_name, "unknown")
        self.assertNotEqual(connection.display_name, "unknown")
def test_simple(self):
        management.get_system_username = lambda: "joe"
        self.assertEqual(management.get_default_username(), "joe")
def test_with_database(self):
        User.objects.create(username="joe")
        management.get_system_username = lambda: "joe"
        self.assertEqual(management.get_default_username(), "")
        self.assertEqual(management.get_default_username(database="other"), "joe")

        User.objects.using("other").create(username="joe")
        self.assertEqual(management.get_default_username(database="other"), "")
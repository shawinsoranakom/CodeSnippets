def test_existing(self):
        User.objects.create(username="joe")
        management.get_system_username = lambda: "joe"
        self.assertEqual(management.get_default_username(), "")
        self.assertEqual(management.get_default_username(check_db=False), "joe")
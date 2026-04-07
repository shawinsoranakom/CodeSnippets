def test_environment_variable_non_interactive(self):
        call_command("createsuperuser", interactive=False, verbosity=0)
        user = User.objects.get(username="test_superuser")
        self.assertEqual(user.email, "joe@somewhere.org")
        self.assertTrue(user.check_password("test_password"))
        # Environment variables are ignored for non-required fields.
        self.assertEqual(user.first_name, "")
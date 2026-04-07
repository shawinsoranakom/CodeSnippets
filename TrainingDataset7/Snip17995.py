def test_ignore_environment_variable_non_interactive(self):
        # Environment variables are ignored in non-interactive mode, if
        # provided by a command line arguments.
        call_command(
            "createsuperuser",
            interactive=False,
            username="cmd_superuser",
            email="cmd@somewhere.org",
            verbosity=0,
        )
        user = User.objects.get(username="cmd_superuser")
        self.assertEqual(user.email, "cmd@somewhere.org")
        self.assertFalse(user.has_usable_password())
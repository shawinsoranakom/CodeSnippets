def test_ignore_environment_variable_interactive(self):
        # Environment variables are ignored in interactive mode.
        @mock_inputs({"password": "cmd_password"})
        def test(self):
            call_command(
                "createsuperuser",
                interactive=True,
                username="cmd_superuser",
                email="cmd@somewhere.org",
                stdin=MockTTY(),
                verbosity=0,
            )
            user = User.objects.get(username="cmd_superuser")
            self.assertEqual(user.email, "cmd@somewhere.org")
            self.assertTrue(user.check_password("cmd_password"))

        test(self)
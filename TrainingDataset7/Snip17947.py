def test_that_changepassword_command_changes_joes_password(self, mock_get_pass):
        """
        Executing the changepassword management command should change joe's
        password
        """
        self.assertTrue(self.user.check_password("qwerty"))

        call_command("changepassword", username="joe", stdout=self.stdout)
        command_output = self.stdout.getvalue().strip()

        self.assertEqual(
            command_output,
            "Changing password for user 'joe'\n"
            "Password changed successfully for user 'joe'",
        )
        self.assertTrue(User.objects.get(username="joe").check_password("not qwerty"))
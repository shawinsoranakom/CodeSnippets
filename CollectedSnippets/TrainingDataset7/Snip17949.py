def test_password_validation(self, mock_get_pass):
        """
        A CommandError should be raised if the user enters in passwords which
        fail validation three times.
        """
        abort_msg = "Aborting password change for user 'joe' after 3 attempts"
        with self.assertRaisesMessage(CommandError, abort_msg):
            call_command(
                "changepassword", username="joe", stdout=self.stdout, stderr=self.stderr
            )
        self.assertIn("This password is entirely numeric.", self.stderr.getvalue())
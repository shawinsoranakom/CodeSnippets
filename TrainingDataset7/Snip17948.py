def test_that_max_tries_exits_1(self, mock_get_pass):
        """
        A CommandError should be thrown by handle() if the user enters in
        mismatched passwords three times.
        """
        msg = "Aborting password change for user 'joe' after 3 attempts"
        with self.assertRaisesMessage(CommandError, msg):
            call_command(
                "changepassword", username="joe", stdout=self.stdout, stderr=self.stderr
            )
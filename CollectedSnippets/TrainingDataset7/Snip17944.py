def test_get_pass_no_input(self, mock_get_pass):
        with self.assertRaisesMessage(CommandError, "aborted"):
            call_command("changepassword", username="joe", stdout=self.stdout)
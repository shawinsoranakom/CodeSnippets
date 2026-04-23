def test_that_changepassword_command_works_with_nonascii_output(
        self, mock_get_pass
    ):
        """
        #21627 -- Executing the changepassword management command should allow
        non-ASCII characters from the User object representation.
        """
        # 'Julia' with accented 'u':
        User.objects.create_user(username="J\xfalia", password="qwerty")
        call_command("changepassword", username="J\xfalia", stdout=self.stdout)
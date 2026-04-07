def test_system_username(self, mock_get_pass):
        """The system username is used if --username isn't provided."""
        username = getpass.getuser()
        User.objects.create_user(username=username, password="qwerty")
        call_command("changepassword", stdout=self.stdout)
        self.assertIs(
            User.objects.get(username=username).check_password("new_password"), True
        )
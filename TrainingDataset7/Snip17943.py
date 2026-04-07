def test_get_pass(self, mock_get_pass):
        call_command("changepassword", username="joe", stdout=self.stdout)
        self.assertIs(User.objects.get(username="joe").check_password("password"), True)
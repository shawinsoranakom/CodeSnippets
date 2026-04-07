def test_password_change_succeeds(self):
        self.login()
        self.client.post(
            "/password_change/",
            {
                "old_password": "password",
                "new_password1": "password1",
                "new_password2": "password1",
            },
        )
        self.fail_login()
        self.login(password="password1")
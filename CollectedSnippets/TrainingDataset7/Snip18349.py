def test_password_change_redirect_default(self):
        self.login()
        response = self.client.post(
            "/password_change/",
            {
                "old_password": "password",
                "new_password1": "password1",
                "new_password2": "password1",
            },
        )
        self.assertRedirects(
            response, "/password_change/done/", fetch_redirect_response=False
        )
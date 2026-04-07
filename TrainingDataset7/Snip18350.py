def test_password_change_redirect_custom(self):
        self.login()
        response = self.client.post(
            "/password_change/custom/",
            {
                "old_password": "password",
                "new_password1": "password1",
                "new_password2": "password1",
            },
        )
        self.assertRedirects(response, "/custom/", fetch_redirect_response=False)
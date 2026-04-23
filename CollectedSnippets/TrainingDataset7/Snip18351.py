def test_password_change_redirect_custom_named(self):
        self.login()
        response = self.client.post(
            "/password_change/custom/named/",
            {
                "old_password": "password",
                "new_password1": "password1",
                "new_password2": "password1",
            },
        )
        self.assertRedirects(
            response, "/password_reset/", fetch_redirect_response=False
        )
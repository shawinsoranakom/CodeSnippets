def test_access_under_login_required_middleware(self):
        response = self.client.post(
            "/password_change/",
            {
                "old_password": "password",
                "new_password1": "password1",
                "new_password2": "password1",
            },
        )
        self.assertRedirects(
            response,
            settings.LOGIN_URL + "?next=/password_change/",
            fetch_redirect_response=False,
        )

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
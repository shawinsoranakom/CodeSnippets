def test_login_form_contains_request(self):
        # The custom authentication form for this login requires a request to
        # initialize it.
        response = self.client.post(
            "/custom_request_auth_login/",
            {
                "username": "testclient",
                "password": "password",
            },
        )
        # The login was successful.
        self.assertRedirects(
            response, settings.LOGIN_REDIRECT_URL, fetch_redirect_response=False
        )
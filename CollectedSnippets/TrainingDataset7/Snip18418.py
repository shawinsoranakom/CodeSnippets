def test_access_under_login_required_middleware(self):
        response = self.client.post("/logout/")
        self.assertRedirects(
            response,
            settings.LOGIN_URL + "?next=/logout/",
            fetch_redirect_response=False,
        )

        self.login()

        response = self.client.post("/logout/")
        self.assertEqual(response.status_code, 200)
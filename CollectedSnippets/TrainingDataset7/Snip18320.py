def test_reset_custom_redirect_named(self):
        response = self.client.post(
            "/password_reset/custom_redirect/named/",
            {"email": "staffmember@example.com"},
        )
        self.assertRedirects(
            response, "/password_reset/", fetch_redirect_response=False
        )
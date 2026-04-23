def test_reset_redirect_default(self):
        response = self.client.post(
            "/password_reset/", {"email": "staffmember@example.com"}
        )
        self.assertRedirects(
            response, "/password_reset/done/", fetch_redirect_response=False
        )
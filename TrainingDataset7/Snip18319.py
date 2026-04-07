def test_reset_custom_redirect(self):
        response = self.client.post(
            "/password_reset/custom_redirect/", {"email": "staffmember@example.com"}
        )
        self.assertRedirects(response, "/custom/", fetch_redirect_response=False)
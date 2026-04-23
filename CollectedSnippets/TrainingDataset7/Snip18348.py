def test_password_change_done_fails(self):
        response = self.client.get("/password_change/done/")
        self.assertRedirects(
            response,
            "/login/?next=/password_change/done/",
            fetch_redirect_response=False,
        )
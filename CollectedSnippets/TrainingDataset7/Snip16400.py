def test_login_redirect_unsafe_next_url_when_logged_in(self):
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("admin:login"),
            query_params={
                REDIRECT_FIELD_NAME: "https://example.com/bad",
            },
        )
        self.assertRedirects(
            response, reverse("admin:index"), fetch_redirect_response=False
        )
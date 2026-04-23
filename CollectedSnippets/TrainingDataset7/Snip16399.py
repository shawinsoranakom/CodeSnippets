def test_login_redirect_to_next_url_when_logged_in(self):
        self.client.force_login(self.superuser)
        next_url = reverse("admin:admin_views_article_add")
        response = self.client.get(
            reverse("admin:login"),
            query_params={REDIRECT_FIELD_NAME: next_url},
        )
        self.assertRedirects(response, next_url)
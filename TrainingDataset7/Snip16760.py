def test_known_url_missing_slash_redirects_with_slash_if_not_auth_no_catch_all_view(
        self,
    ):
        known_url = reverse("admin10:admin_views_article_changelist")
        response = self.client.get(known_url[:-1])
        self.assertRedirects(
            response, known_url, status_code=301, fetch_redirect_response=False
        )
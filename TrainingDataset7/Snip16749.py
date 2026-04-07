def test_missing_slash_append_slash_true_query_string(self):
        self.client.force_login(self.staff_user)
        known_url = reverse("admin:admin_views_article_changelist")
        response = self.client.get("%s?id=1" % known_url[:-1])
        self.assertRedirects(
            response,
            f"{known_url}?id=1",
            status_code=301,
            fetch_redirect_response=False,
        )
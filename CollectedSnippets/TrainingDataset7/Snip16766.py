def test_missing_slash_append_slash_true_query_without_final_catch_all_view(self):
        self.client.force_login(self.staff_user)
        known_url = reverse("admin10:admin_views_article_changelist")
        response = self.client.get("%s?id=1" % known_url[:-1])
        self.assertRedirects(
            response,
            f"{known_url}?id=1",
            status_code=301,
            fetch_redirect_response=False,
        )
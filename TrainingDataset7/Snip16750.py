def test_missing_slash_append_slash_true_script_name(self):
        self.client.force_login(self.staff_user)
        known_url = reverse("admin:admin_views_article_changelist")
        response = self.client.get(known_url[:-1], SCRIPT_NAME="/prefix/")
        self.assertRedirects(
            response,
            "/prefix" + known_url,
            status_code=301,
            fetch_redirect_response=False,
        )
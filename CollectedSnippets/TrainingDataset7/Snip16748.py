def test_missing_slash_append_slash_true(self):
        self.client.force_login(self.staff_user)
        known_url = reverse("admin:admin_views_article_changelist")
        response = self.client.get(known_url[:-1])
        self.assertRedirects(
            response, known_url, status_code=301, target_status_code=403
        )
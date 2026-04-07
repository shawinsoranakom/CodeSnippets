def test_missing_slash_append_slash_true_non_staff_user(self):
        self.client.force_login(self.non_staff_user)
        known_url = reverse("admin:admin_views_article_changelist")
        response = self.client.get(known_url[:-1])
        self.assertRedirects(
            response,
            "/test_admin/admin/login/?next=/test_admin/admin/admin_views/article",
        )
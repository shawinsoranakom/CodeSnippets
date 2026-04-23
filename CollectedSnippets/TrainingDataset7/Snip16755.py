def test_missing_slash_append_slash_false(self):
        self.client.force_login(self.staff_user)
        known_url = reverse("admin:admin_views_article_changelist")
        response = self.client.get(known_url[:-1])
        self.assertEqual(response.status_code, 404)
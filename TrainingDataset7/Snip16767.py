def test_missing_slash_append_slash_false_without_final_catch_all_view(self):
        self.client.force_login(self.staff_user)
        known_url = reverse("admin10:admin_views_article_changelist")
        response = self.client.get(known_url[:-1])
        self.assertEqual(response.status_code, 404)
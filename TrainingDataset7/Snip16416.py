def test_delete_view_nonexistent_obj(self):
        self.client.force_login(self.deleteuser)
        url = reverse("admin:admin_views_article_delete", args=("nonexistent",))
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse("admin:index"))
        self.assertEqual(
            [m.message for m in response.context["messages"]],
            ["article with ID “nonexistent” doesn’t exist. Perhaps it was deleted?"],
        )
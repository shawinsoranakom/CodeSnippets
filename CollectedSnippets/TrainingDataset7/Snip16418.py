def test_history_view_bad_url(self):
        self.client.force_login(self.changeuser)
        response = self.client.get(
            reverse("admin:admin_views_article_history", args=("foo",)), follow=True
        )
        self.assertRedirects(response, reverse("admin:index"))
        self.assertEqual(
            [m.message for m in response.context["messages"]],
            ["article with ID “foo” doesn’t exist. Perhaps it was deleted?"],
        )
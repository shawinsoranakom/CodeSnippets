def test_change_view_subtitle_per_object(self):
        response = self.client.get(
            reverse("admin:admin_views_article_change", args=(self.a1.pk,)),
        )
        self.assertContains(
            response,
            "<title>Article 1 | Change article | Django site admin</title>",
        )
        self.assertContains(response, "<h1>Change article</h1>")
        self.assertContains(response, "<h2>Article 1</h2>")
        response = self.client.get(
            reverse("admin:admin_views_article_change", args=(self.a2.pk,)),
        )
        self.assertContains(
            response,
            "<title>Article 2 | Change article | Django site admin</title>",
        )
        self.assertContains(response, "<h1>Change article</h1>")
        self.assertContains(response, "<h2>Article 2</h2>")
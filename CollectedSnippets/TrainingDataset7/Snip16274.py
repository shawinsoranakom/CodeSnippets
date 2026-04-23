def test_trailing_slash_required(self):
        """
        If you leave off the trailing slash, app should redirect and add it.
        """
        add_url = reverse("admin:admin_views_article_add")
        response = self.client.get(add_url[:-1])
        self.assertRedirects(response, add_url, status_code=301)
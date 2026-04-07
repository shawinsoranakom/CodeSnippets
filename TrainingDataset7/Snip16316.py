def test_isnull_lookups(self):
        """Ensure is_null is handled correctly."""
        Article.objects.create(
            title="I Could Go Anywhere",
            content="Versatile",
            date=datetime.datetime.now(),
        )
        changelist_url = reverse("admin:admin_views_article_changelist")
        response = self.client.get(changelist_url)
        self.assertContains(response, "4 articles")
        response = self.client.get(changelist_url, {"section__isnull": "false"})
        self.assertContains(response, "3 articles")
        response = self.client.get(changelist_url, {"section__isnull": "0"})
        self.assertContains(response, "3 articles")
        response = self.client.get(changelist_url, {"section__isnull": "true"})
        self.assertContains(response, "1 article")
        response = self.client.get(changelist_url, {"section__isnull": "1"})
        self.assertContains(response, "1 article")
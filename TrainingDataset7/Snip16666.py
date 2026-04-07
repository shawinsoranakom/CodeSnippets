def test_empty(self):
        """
        No date hierarchy links display with empty changelist.
        """
        response = self.client.get(reverse("admin:admin_views_podcast_changelist"))
        self.assertNotContains(response, "release_date__year=")
        self.assertNotContains(response, "release_date__month=")
        self.assertNotContains(response, "release_date__day=")
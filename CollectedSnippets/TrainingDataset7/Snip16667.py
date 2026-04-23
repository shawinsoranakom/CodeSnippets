def test_single(self):
        """
        Single day-level date hierarchy appears for single object.
        """
        DATE = datetime.date(2000, 6, 30)
        Podcast.objects.create(release_date=DATE)
        url = reverse("admin:admin_views_podcast_changelist")
        response = self.client.get(url)
        self.assert_contains_day_link(response, DATE)
        self.assert_non_localized_year(response, 2000)
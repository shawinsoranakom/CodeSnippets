def test_within_month(self):
        """
        day-level links appear for changelist within single month.
        """
        DATES = (
            datetime.date(2000, 6, 30),
            datetime.date(2000, 6, 15),
            datetime.date(2000, 6, 3),
        )
        for date in DATES:
            Podcast.objects.create(release_date=date)
        url = reverse("admin:admin_views_podcast_changelist")
        response = self.client.get(url)
        for date in DATES:
            self.assert_contains_day_link(response, date)
        self.assert_non_localized_year(response, 2000)
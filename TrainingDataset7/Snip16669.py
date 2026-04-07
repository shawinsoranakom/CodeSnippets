def test_within_year(self):
        """
        month-level links appear for changelist within single year.
        """
        DATES = (
            datetime.date(2000, 1, 30),
            datetime.date(2000, 3, 15),
            datetime.date(2000, 5, 3),
        )
        for date in DATES:
            Podcast.objects.create(release_date=date)
        url = reverse("admin:admin_views_podcast_changelist")
        response = self.client.get(url)
        # no day-level links
        self.assertNotContains(response, "release_date__day=")
        for date in DATES:
            self.assert_contains_month_link(response, date)
        self.assert_non_localized_year(response, 2000)
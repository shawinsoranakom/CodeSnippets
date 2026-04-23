def test_multiple_years(self):
        """
        year-level links appear for year-spanning changelist.
        """
        DATES = (
            datetime.date(2001, 1, 30),
            datetime.date(2003, 3, 15),
            datetime.date(2005, 5, 3),
        )
        for date in DATES:
            Podcast.objects.create(release_date=date)
        response = self.client.get(reverse("admin:admin_views_podcast_changelist"))
        # no day/month-level links
        self.assertNotContains(response, "release_date__day=")
        self.assertNotContains(response, "release_date__month=")
        for date in DATES:
            self.assert_contains_year_link(response, date)

        # and make sure GET parameters still behave correctly
        for date in DATES:
            url = "%s?release_date__year=%d" % (
                reverse("admin:admin_views_podcast_changelist"),
                date.year,
            )
            response = self.client.get(url)
            self.assert_contains_month_link(response, date)
            self.assert_non_localized_year(response, 2000)
            self.assert_non_localized_year(response, 2003)
            self.assert_non_localized_year(response, 2005)

            url = "%s?release_date__year=%d&release_date__month=%d" % (
                reverse("admin:admin_views_podcast_changelist"),
                date.year,
                date.month,
            )
            response = self.client.get(url)
            self.assert_contains_day_link(response, date)
            self.assert_non_localized_year(response, 2000)
            self.assert_non_localized_year(response, 2003)
            self.assert_non_localized_year(response, 2005)
def test_latest_post_date_returns_utc_time(self):
        for use_tz in (True, False):
            with self.settings(USE_TZ=use_tz):
                rss_feed = feedgenerator.Rss201rev2Feed("title", "link", "description")
                self.assertEqual(
                    rss_feed.latest_post_date().tzinfo,
                    datetime.UTC,
                )
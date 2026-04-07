def test_rss2_multiple_enclosures(self):
        with self.assertRaisesMessage(
            ValueError,
            "RSS feed items may only have one enclosure, see "
            "http://www.rssboard.org/rss-profile#element-channel-item-enclosure",
        ):
            self.client.get("/syndication/rss2/multiple-enclosure/")
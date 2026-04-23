def test_rss_mime_type(self):
        """
        RSS MIME type has UTF8 Charset parameter set
        """
        rss_feed = feedgenerator.Rss201rev2Feed("title", "link", "description")
        self.assertEqual(rss_feed.content_type, "application/rss+xml; charset=utf-8")
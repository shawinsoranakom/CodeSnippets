def test_feed_without_feed_url_gets_rendered_without_atom_link(self):
        feed = feedgenerator.Rss201rev2Feed("title", "/link/", "descr")
        self.assertIsNone(feed.feed["feed_url"])
        feed_content = feed.writeString("utf-8")
        self.assertNotIn("<atom:link", feed_content)
        self.assertNotIn('href="/feed/"', feed_content)
        self.assertNotIn('rel="self"', feed_content)
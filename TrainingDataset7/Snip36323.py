def test_feed_with_feed_url_gets_rendered_with_atom_link(self):
        feed = feedgenerator.Rss201rev2Feed(
            "title", "/link/", "descr", feed_url="/feed/"
        )
        self.assertEqual(feed.feed["feed_url"], "/feed/")
        feed_content = feed.writeString("utf-8")
        self.assertIn("<atom:link", feed_content)
        self.assertIn('href="/feed/"', feed_content)
        self.assertIn('rel="self"', feed_content)
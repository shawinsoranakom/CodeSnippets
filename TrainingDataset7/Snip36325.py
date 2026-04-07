def test_deterministic_attribute_order(self):
        feed = feedgenerator.Atom1Feed("title", "/link/", "desc")
        feed_content = feed.writeString("utf-8")
        self.assertIn('href="/link/" rel="alternate"', feed_content)
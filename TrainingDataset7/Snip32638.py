def test_feed_no_content_self_closing_tag(self):
        tests = [
            (Atom1Feed, "link"),
            (Rss201rev2Feed, "atom:link"),
        ]
        for feedgenerator, tag in tests:
            with self.subTest(feedgenerator=feedgenerator.__name__):
                feed = feedgenerator(
                    title="title",
                    link="https://example.com",
                    description="self closing tags test",
                    feed_url="https://feed.url.com",
                )
                doc = feed.writeString("utf-8")
                self.assertIn(f'<{tag} href="https://feed.url.com" rel="self"/>', doc)
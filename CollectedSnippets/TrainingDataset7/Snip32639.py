def test_stylesheets_none(self):
        feed = Rss201rev2Feed(
            title="test",
            link="https://example.com",
            description="test",
            stylesheets=None,
        )
        self.assertNotIn("xml-stylesheet", feed.writeString("utf-8"))
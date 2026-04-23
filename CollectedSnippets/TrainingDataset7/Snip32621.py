def test_rss2_feed_with_decorated_methods(self):
        response = self.client.get("/syndication/rss2/with-decorated-methods/")
        doc = minidom.parseString(response.content)
        chan = doc.getElementsByTagName("rss")[0].getElementsByTagName("channel")[0]
        self.assertCategories(chan, ["javascript", "vue"])
        self.assertChildNodeContent(
            chan,
            {
                "title": "Overridden title -- decorated by @wraps.",
                "description": "Overridden description -- decorated by @wraps.",
                "ttl": "800 -- decorated by @wraps.",
                "copyright": "Copyright (c) 2022, John Doe -- decorated by @wraps.",
            },
        )
        items = chan.getElementsByTagName("item")
        self.assertChildNodeContent(
            items[0],
            {
                "title": (
                    f"Overridden item title: {self.e1.title} -- decorated by @wraps."
                ),
                "description": "Overridden item description -- decorated by @wraps.",
            },
        )
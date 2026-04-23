def test_rss2_feed_with_wrong_decorated_methods(self):
        msg = (
            "Feed method 'item_description' decorated by 'wrapper' needs to use "
            "@functools.wraps."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.client.get("/syndication/rss2/with-wrong-decorated-methods/")
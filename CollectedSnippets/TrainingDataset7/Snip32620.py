def test_rss2_feed_with_callable_object(self):
        response = self.client.get("/syndication/rss2/with-callable-object/")
        doc = minidom.parseString(response.content)
        chan = doc.getElementsByTagName("rss")[0].getElementsByTagName("channel")[0]
        self.assertChildNodeContent(chan, {"ttl": "700"})
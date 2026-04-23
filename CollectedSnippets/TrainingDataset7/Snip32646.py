def test_feed_url(self):
        """
        The feed_url can be overridden.
        """
        response = self.client.get("/syndication/feedurl/")
        doc = minidom.parseString(response.content)
        for link in doc.getElementsByTagName("link"):
            if link.getAttribute("rel") == "self":
                self.assertEqual(
                    link.getAttribute("href"), "http://example.com/customfeedurl/"
                )
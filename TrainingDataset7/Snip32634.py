def test_feed_generator_language_attribute(self):
        response = self.client.get("/syndication/language/")
        feed = minidom.parseString(response.content).firstChild
        self.assertEqual(
            feed.firstChild.getElementsByTagName("language")[0].firstChild.nodeValue,
            "de",
        )
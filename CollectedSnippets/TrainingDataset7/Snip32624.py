def test_rss2_feed_guid_permalink_true(self):
        """
        Test if the 'isPermaLink' attribute of <guid> element of an item
        in the RSS feed is 'true'.
        """
        response = self.client.get("/syndication/rss2/guid_ispermalink_true/")
        doc = minidom.parseString(response.content)
        chan = doc.getElementsByTagName("rss")[0].getElementsByTagName("channel")[0]
        items = chan.getElementsByTagName("item")
        for item in items:
            self.assertEqual(
                item.getElementsByTagName("guid")[0]
                .attributes.get("isPermaLink")
                .value,
                "true",
            )
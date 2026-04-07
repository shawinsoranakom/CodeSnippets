def test_geofeed_rss(self):
        "Tests geographic feeds using GeoRSS over RSSv2."
        # Uses `GEOSGeometry` in `item_geometry`
        doc1 = minidom.parseString(self.client.get("/feeds/rss1/").content)
        # Uses a 2-tuple in `item_geometry`
        doc2 = minidom.parseString(self.client.get("/feeds/rss2/").content)
        feed1, feed2 = doc1.firstChild, doc2.firstChild

        # Making sure the box got added to the second GeoRSS feed.
        self.assertChildNodes(
            feed2.getElementsByTagName("channel")[0],
            [
                "title",
                "link",
                "description",
                "language",
                "lastBuildDate",
                "item",
                "georss:box",
                "atom:link",
            ],
        )

        # Incrementing through the feeds.
        for feed in [feed1, feed2]:
            # Ensuring the georss namespace was added to the <rss> element.
            self.assertEqual(
                feed.getAttribute("xmlns:georss"), "http://www.georss.org/georss"
            )
            chan = feed.getElementsByTagName("channel")[0]
            items = chan.getElementsByTagName("item")
            self.assertEqual(len(items), City.objects.count())

            # Ensuring the georss element was added to each item in the feed.
            for item in items:
                self.assertChildNodes(
                    item, ["title", "link", "description", "guid", "georss:point"]
                )
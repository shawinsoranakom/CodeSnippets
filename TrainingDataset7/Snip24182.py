def test_geofeed_w3c(self):
        "Testing geographic feeds using W3C Geo."
        doc = minidom.parseString(self.client.get("/feeds/w3cgeo1/").content)
        feed = doc.firstChild
        # Ensuring the geo namespace was added to the <feed> element.
        self.assertEqual(
            feed.getAttribute("xmlns:geo"), "http://www.w3.org/2003/01/geo/wgs84_pos#"
        )
        chan = feed.getElementsByTagName("channel")[0]
        items = chan.getElementsByTagName("item")
        self.assertEqual(len(items), City.objects.count())

        # Ensuring the geo:lat and geo:lon element was added to each item in
        # the feed.
        for item in items:
            self.assertChildNodes(
                item, ["title", "link", "description", "guid", "geo:lat", "geo:lon"]
            )

        # Boxes and Polygons aren't allowed in W3C Geo feeds.
        with self.assertRaises(ValueError):  # Box in <channel>
            self.client.get("/feeds/w3cgeo2/")
        with self.assertRaises(ValueError):  # Polygons in <entry>
            self.client.get("/feeds/w3cgeo3/")
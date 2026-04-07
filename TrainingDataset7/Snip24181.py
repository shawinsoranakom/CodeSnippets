def test_geofeed_atom(self):
        "Testing geographic feeds using GeoRSS over Atom."
        doc1 = minidom.parseString(self.client.get("/feeds/atom1/").content)
        doc2 = minidom.parseString(self.client.get("/feeds/atom2/").content)
        feed1, feed2 = doc1.firstChild, doc2.firstChild

        # Making sure the box got added to the second GeoRSS feed.
        self.assertChildNodes(
            feed2, ["title", "link", "id", "updated", "entry", "georss:box"]
        )

        for feed in [feed1, feed2]:
            # Ensuring the georsss namespace was added to the <feed> element.
            self.assertEqual(
                feed.getAttribute("xmlns:georss"), "http://www.georss.org/georss"
            )
            entries = feed.getElementsByTagName("entry")
            self.assertEqual(len(entries), City.objects.count())

            # Ensuring the georss element was added to each entry in the feed.
            for entry in entries:
                self.assertChildNodes(
                    entry, ["title", "link", "id", "summary", "georss:point"]
                )
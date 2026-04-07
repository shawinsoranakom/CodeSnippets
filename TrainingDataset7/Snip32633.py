def test_custom_feed_generator(self):
        response = self.client.get("/syndication/custom/")
        feed = minidom.parseString(response.content).firstChild

        self.assertEqual(feed.nodeName, "feed")
        self.assertEqual(feed.getAttribute("django"), "rocks")
        self.assertChildNodes(
            feed,
            [
                "title",
                "subtitle",
                "link",
                "id",
                "updated",
                "entry",
                "spam",
                "rights",
                "category",
                "author",
            ],
        )

        entries = feed.getElementsByTagName("entry")
        self.assertEqual(len(entries), Entry.objects.count())
        for entry in entries:
            self.assertEqual(entry.getAttribute("bacon"), "yum")
            self.assertChildNodes(
                entry,
                [
                    "title",
                    "link",
                    "id",
                    "summary",
                    "ministry",
                    "rights",
                    "author",
                    "updated",
                    "published",
                    "category",
                ],
            )
            summary = entry.getElementsByTagName("summary")[0]
            self.assertEqual(summary.getAttribute("type"), "html")
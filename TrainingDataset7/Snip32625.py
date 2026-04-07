def test_rss2_single_enclosure(self):
        response = self.client.get("/syndication/rss2/single-enclosure/")
        doc = minidom.parseString(response.content)
        chan = doc.getElementsByTagName("rss")[0].getElementsByTagName("channel")[0]
        items = chan.getElementsByTagName("item")
        for item in items:
            enclosures = item.getElementsByTagName("enclosure")
            self.assertEqual(len(enclosures), 1)
def test_atom_multiple_enclosures(self):
        response = self.client.get("/syndication/atom/multiple-enclosure/")
        feed = minidom.parseString(response.content).firstChild
        items = feed.getElementsByTagName("entry")
        for item in items:
            links = item.getElementsByTagName("link")
            links = [link for link in links if link.getAttribute("rel") == "enclosure"]
            self.assertEqual(len(links), 2)
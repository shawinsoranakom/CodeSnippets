def test_atom_single_enclosure(self):
        response = self.client.get("/syndication/atom/single-enclosure/")
        feed = minidom.parseString(response.content).firstChild
        items = feed.getElementsByTagName("entry")
        for item in items:
            links = item.getElementsByTagName("link")
            links = [link for link in links if link.getAttribute("rel") == "enclosure"]
            self.assertEqual(len(links), 1)
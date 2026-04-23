def test_atom_feed_published_and_updated_elements(self):
        """
        The published and updated elements are not
        the same and now adhere to RFC 4287.
        """
        response = self.client.get("/syndication/atom/")
        feed = minidom.parseString(response.content).firstChild
        entries = feed.getElementsByTagName("entry")

        published = entries[0].getElementsByTagName("published")[0].firstChild.wholeText
        updated = entries[0].getElementsByTagName("updated")[0].firstChild.wholeText

        self.assertNotEqual(published, updated)
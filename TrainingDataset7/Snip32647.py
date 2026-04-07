def test_secure_urls(self):
        """
        Test URLs are prefixed with https:// when feed is requested over HTTPS.
        """
        response = self.client.get(
            "/syndication/rss2/",
            **{
                "wsgi.url_scheme": "https",
            },
        )
        doc = minidom.parseString(response.content)
        chan = doc.getElementsByTagName("channel")[0]
        self.assertEqual(
            chan.getElementsByTagName("link")[0].firstChild.wholeText[0:5], "https"
        )
        atom_link = chan.getElementsByTagName("atom:link")[0]
        self.assertEqual(atom_link.getAttribute("href")[0:5], "https")
        for link in doc.getElementsByTagName("link"):
            if link.getAttribute("rel") == "self":
                self.assertEqual(link.getAttribute("href")[0:5], "https")
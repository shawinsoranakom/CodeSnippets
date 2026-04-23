def test_title_escaping(self):
        """
        Titles are escaped correctly in RSS feeds.
        """
        response = self.client.get("/syndication/rss2/")
        doc = minidom.parseString(response.content)
        for item in doc.getElementsByTagName("item"):
            link = item.getElementsByTagName("link")[0]
            if link.firstChild.wholeText == "http://example.com/blog/4/":
                title = item.getElementsByTagName("title")[0]
                self.assertEqual(title.firstChild.wholeText, "A &amp; B &lt; C &gt; D")
def test_template_feed(self):
        """
        The item title and description can be overridden with templates.
        """
        response = self.client.get("/syndication/template/")
        doc = minidom.parseString(response.content)
        feed = doc.getElementsByTagName("rss")[0]
        chan = feed.getElementsByTagName("channel")[0]
        items = chan.getElementsByTagName("item")

        self.assertChildNodeContent(
            items[0],
            {
                "title": "Title in your templates: My first entry\n",
                "description": "Description in your templates: My first entry\n",
                "link": "http://example.com/blog/%s/" % self.e1.pk,
            },
        )
def test_template_context_feed(self):
        """
        Custom context data can be passed to templates for title
        and description.
        """
        response = self.client.get("/syndication/template_context/")
        doc = minidom.parseString(response.content)
        feed = doc.getElementsByTagName("rss")[0]
        chan = feed.getElementsByTagName("channel")[0]
        items = chan.getElementsByTagName("item")

        self.assertChildNodeContent(
            items[0],
            {
                "title": "My first entry (foo is bar)\n",
                "description": "My first entry (foo is bar)\n",
            },
        )
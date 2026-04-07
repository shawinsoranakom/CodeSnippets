def test_get_object(self):
        response = self.client.get("/syndication/rss2/articles/%s/" % self.e1.pk)
        doc = minidom.parseString(response.content)
        feed = doc.getElementsByTagName("rss")[0]
        chan = feed.getElementsByTagName("channel")[0]
        items = chan.getElementsByTagName("item")

        self.assertChildNodeContent(
            items[0],
            {
                "comments": "/blog/%s/article/%s/comments" % (self.e1.pk, self.a1.pk),
                "description": "Article description: My first article",
                "link": "http://example.com/blog/%s/article/%s/"
                % (self.e1.pk, self.a1.pk),
                "title": "Title: My first article",
                "pubDate": rfc2822_date(timezone.make_aware(self.a1.published, TZ)),
            },
        )
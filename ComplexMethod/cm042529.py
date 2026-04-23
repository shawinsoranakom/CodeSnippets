def test_xmliter_namespaces(self):
        body = b"""
            <?xml version="1.0" encoding="UTF-8"?>
            <rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">
                <channel>
                <title>My Dummy Company</title>
                <link>http://www.mydummycompany.com</link>
                <description>This is a dummy company. We do nothing.</description>
                <item>
                    <title>Item 1</title>
                    <description>This is item 1</description>
                    <link>http://www.mydummycompany.com/items/1</link>
                    <g:image_link>http://www.mydummycompany.com/images/item1.jpg</g:image_link>
                    <g:id>ITEM_1</g:id>
                    <g:price>400</g:price>
                </item>
                </channel>
            </rss>
        """
        response = XmlResponse(url="http://mydummycompany.com", body=body)
        my_iter = self.xmliter(response, "item")
        node = next(my_iter)
        node.register_namespace("g", "http://base.google.com/ns/1.0")
        assert node.xpath("title/text()").getall() == ["Item 1"]
        assert node.xpath("description/text()").getall() == ["This is item 1"]
        assert node.xpath("link/text()").getall() == [
            "http://www.mydummycompany.com/items/1"
        ]
        assert node.xpath("g:image_link/text()").getall() == [
            "http://www.mydummycompany.com/images/item1.jpg"
        ]
        assert node.xpath("g:id/text()").getall() == ["ITEM_1"]
        assert node.xpath("g:price/text()").getall() == ["400"]
        assert node.xpath("image_link/text()").getall() == []
        assert node.xpath("id/text()").getall() == []
        assert node.xpath("price/text()").getall() == []
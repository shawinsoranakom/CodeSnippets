def test_stylesheets_instructions_are_at_the_top(self):
        response = self.client.get("/syndication/stylesheet/")
        doc = minidom.parseString(response.content)
        self.assertEqual(doc.childNodes[0].nodeName, "xml-stylesheet")
        self.assertEqual(
            doc.childNodes[0].data,
            'href="/stylesheet1.xsl" media="screen" type="text/xsl"',
        )
        self.assertEqual(doc.childNodes[1].nodeName, "xml-stylesheet")
        self.assertEqual(
            doc.childNodes[1].data,
            'href="/stylesheet2.xsl" media="screen" type="text/xsl"',
        )
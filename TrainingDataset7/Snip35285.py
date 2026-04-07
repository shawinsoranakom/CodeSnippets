def test_simple_equal_unordered(self):
        xml1 = "<elem attr1='a' attr2='b' />"
        xml2 = "<elem attr2='b' attr1='a' />"
        self.assertXMLEqual(xml1, xml2)
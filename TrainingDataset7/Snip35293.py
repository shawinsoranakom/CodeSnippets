def test_simple_not_equal_with_whitespace_in_the_middle(self):
        xml1 = "<elem>foo</elem><elem>bar</elem>"
        xml2 = "<elem>foo</elem> <elem>bar</elem>"
        self.assertXMLNotEqual(xml1, xml2)
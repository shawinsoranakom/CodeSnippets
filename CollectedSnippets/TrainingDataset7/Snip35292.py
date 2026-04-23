def test_simple_equal_with_leading_or_trailing_whitespace(self):
        xml1 = "<elem>foo</elem> \t\n"
        xml2 = " \t\n<elem>foo</elem>"
        self.assertXMLEqual(xml1, xml2)
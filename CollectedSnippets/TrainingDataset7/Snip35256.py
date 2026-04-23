def test_boolean_attribute(self):
        html1 = "<input checked>"
        html2 = '<input checked="">'
        html3 = '<input checked="checked">'
        self.assertHTMLEqual(html1, html2)
        self.assertHTMLEqual(html1, html3)
        self.assertHTMLEqual(html2, html3)
        self.assertHTMLNotEqual(html1, '<input checked="invalid">')
        self.assertEqual(str(parse_html(html1)), "<input checked>")
        self.assertEqual(str(parse_html(html2)), "<input checked>")
        self.assertEqual(str(parse_html(html3)), "<input checked>")
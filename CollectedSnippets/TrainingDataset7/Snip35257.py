def test_non_boolean_attibutes(self):
        html1 = "<input value>"
        html2 = '<input value="">'
        html3 = '<input value="value">'
        self.assertHTMLEqual(html1, html2)
        self.assertHTMLNotEqual(html1, html3)
        self.assertEqual(str(parse_html(html1)), '<input value="">')
        self.assertEqual(str(parse_html(html2)), '<input value="">')
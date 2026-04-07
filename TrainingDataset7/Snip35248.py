def test_html_parser(self):
        element = parse_html("<div><p>Hello</p></div>")
        self.assertEqual(len(element.children), 1)
        self.assertEqual(element.children[0].name, "p")
        self.assertEqual(element.children[0].children[0], "Hello")

        parse_html("<p>")
        parse_html("<p attr>")
        dom = parse_html("<p>foo")
        self.assertEqual(len(dom.children), 1)
        self.assertEqual(dom.name, "p")
        self.assertEqual(dom[0], "foo")
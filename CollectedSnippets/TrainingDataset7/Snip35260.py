def test_html_contain(self):
        # equal html contains each other
        dom1 = parse_html("<p>foo")
        dom2 = parse_html("<p>foo</p>")
        self.assertIn(dom1, dom2)
        self.assertIn(dom2, dom1)

        dom2 = parse_html("<div><p>foo</p></div>")
        self.assertIn(dom1, dom2)
        self.assertNotIn(dom2, dom1)

        self.assertNotIn("<p>foo</p>", dom2)
        self.assertIn("foo", dom2)

        # when a root element is used ...
        dom1 = parse_html("<p>foo</p><p>bar</p>")
        dom2 = parse_html("<p>foo</p><p>bar</p>")
        self.assertIn(dom1, dom2)
        dom1 = parse_html("<p>foo</p>")
        self.assertIn(dom1, dom2)
        dom1 = parse_html("<p>bar</p>")
        self.assertIn(dom1, dom2)
        dom1 = parse_html("<div><p>foo</p><p>bar</p></div>")
        self.assertIn(dom2, dom1)
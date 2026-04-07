def test_count(self):
        # equal html contains each other one time
        dom1 = parse_html("<p>foo")
        dom2 = parse_html("<p>foo</p>")
        self.assertEqual(dom1.count(dom2), 1)
        self.assertEqual(dom2.count(dom1), 1)

        dom2 = parse_html("<p>foo</p><p>bar</p>")
        self.assertEqual(dom2.count(dom1), 1)

        dom2 = parse_html("<p>foo foo</p><p>foo</p>")
        self.assertEqual(dom2.count("foo"), 3)

        dom2 = parse_html('<p class="bar">foo</p>')
        self.assertEqual(dom2.count("bar"), 0)
        self.assertEqual(dom2.count("class"), 0)
        self.assertEqual(dom2.count("p"), 0)
        self.assertEqual(dom2.count("o"), 2)

        dom2 = parse_html("<p>foo</p><p>foo</p>")
        self.assertEqual(dom2.count(dom1), 2)

        dom2 = parse_html('<div><p>foo<input type=""></p><p>foo</p></div>')
        self.assertEqual(dom2.count(dom1), 1)

        dom2 = parse_html("<div><div><p>foo</p></div></div>")
        self.assertEqual(dom2.count(dom1), 1)

        dom2 = parse_html("<p>foo<p>foo</p></p>")
        self.assertEqual(dom2.count(dom1), 1)

        dom2 = parse_html("<p>foo<p>bar</p></p>")
        self.assertEqual(dom2.count(dom1), 0)

        # HTML with a root element contains the same HTML with no root element.
        dom1 = parse_html("<p>foo</p><p>bar</p>")
        dom2 = parse_html("<div><p>foo</p><p>bar</p></div>")
        self.assertEqual(dom2.count(dom1), 1)

        # Target of search is a sequence of child elements and appears more
        # than once.
        dom2 = parse_html("<div><p>foo</p><p>bar</p><p>foo</p><p>bar</p></div>")
        self.assertEqual(dom2.count(dom1), 2)

        # Searched HTML has additional children.
        dom1 = parse_html("<a/><b/>")
        dom2 = parse_html("<a/><b/><c/>")
        self.assertEqual(dom2.count(dom1), 1)

        # No match found in children.
        dom1 = parse_html("<b/><a/>")
        self.assertEqual(dom2.count(dom1), 0)

        # Target of search found among children and grandchildren.
        dom1 = parse_html("<b/><b/>")
        dom2 = parse_html("<a><b/><b/></a><b/><b/>")
        self.assertEqual(dom2.count(dom1), 2)
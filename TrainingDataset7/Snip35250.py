def test_void_elements(self):
        for tag in VOID_ELEMENTS:
            with self.subTest(tag):
                dom = parse_html("<p>Hello <%s> world</p>" % tag)
                self.assertEqual(len(dom.children), 3)
                self.assertEqual(dom[0], "Hello")
                self.assertEqual(dom[1].name, tag)
                self.assertEqual(dom[2], "world")

                dom = parse_html("<p>Hello <%s /> world</p>" % tag)
                self.assertEqual(len(dom.children), 3)
                self.assertEqual(dom[0], "Hello")
                self.assertEqual(dom[1].name, tag)
                self.assertEqual(dom[2], "world")
def test_simple_tag_format_html_escaping(self):
        # Check we don't double escape
        c = Context({"name": "Jack & Jill"})
        t = self.engine.from_string("{% load custom %}{% escape_format_html %}")
        self.assertEqual(t.render(c), "Hello Jack &amp; Jill!")
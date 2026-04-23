def test_simple_tag_explicit_escaping(self):
        # Check we don't double escape
        c = Context({"name": "Jack & Jill"})
        t = self.engine.from_string("{% load custom %}{% escape_explicit %}")
        self.assertEqual(t.render(c), "Hello Jack &amp; Jill!")
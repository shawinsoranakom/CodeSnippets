def test_simple_tag_naive_escaping(self):
        c = Context({"name": "Jack & Jill"})
        t = self.engine.from_string("{% load custom %}{% escape_naive %}")
        self.assertEqual(t.render(c), "Hello Jack &amp; Jill!")
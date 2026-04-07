def test_simple_tag_escaping_autoescape_off(self):
        c = Context({"name": "Jack & Jill"}, autoescape=False)
        t = self.engine.from_string("{% load custom %}{% escape_naive %}")
        self.assertEqual(t.render(c), "Hello Jack & Jill!")
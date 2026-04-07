def test_simple_block_tag_escaping_autoescape_off(self):
        c = Context({"name": "Jack & Jill"}, autoescape=False)
        t = self.engine.from_string(
            "{% load custom %}{% escape_naive_block %}{{ name }} again"
            "{% endescape_naive_block %}"
        )
        self.assertEqual(t.render(c), "Hello Jack & Jill: Jack & Jill again!")
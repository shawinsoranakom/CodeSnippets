def test_simple_block_tag_explicit_escaping(self):
        # Check we don't double escape
        c = Context({"name": "Jack & Jill"})
        t = self.engine.from_string(
            "{% load custom %}{% escape_explicit_block %}again"
            "{% endescape_explicit_block %}"
        )
        self.assertEqual(t.render(c), "Hello Jack &amp; Jill: again!")
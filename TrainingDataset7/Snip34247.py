def test_simple_block_tag_naive_escaping(self):
        c = Context({"name": "Jack & Jill"})
        t = self.engine.from_string(
            "{% load custom %}{% escape_naive_block %}{{ name }} again"
            "{% endescape_naive_block %}"
        )
        self.assertEqual(
            t.render(c), "Hello Jack &amp; Jill: Jack &amp;amp; Jill again!"
        )
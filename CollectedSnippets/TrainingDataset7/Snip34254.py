def test_simple_block_gets_context(self):
        c = Context({"name": "Jack & Jill"})
        t = self.engine.from_string("{% load custom %}{% div %}{{ name }}{% enddiv %}")
        self.assertEqual(t.render(c), "<div id='test'>Jack &amp; Jill</div>")
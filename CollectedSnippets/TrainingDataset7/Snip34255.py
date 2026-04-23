def test_simple_block_capture_as(self):
        c = Context({"name": "Jack & Jill"})
        t = self.engine.from_string(
            "{% load custom %}{% div as div_content %}{{ name }}{% enddiv %}"
            "My div is: {{ div_content }}"
        )
        self.assertEqual(t.render(c), "My div is: <div id='test'>Jack &amp; Jill</div>")
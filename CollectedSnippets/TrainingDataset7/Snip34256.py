def test_simple_block_nested(self):
        c = Context({"name": "Jack & Jill"})
        t = self.engine.from_string(
            "{% load custom %}Start{% div id='outer' %}Before{% div id='inner' %}"
            "{{ name }}{% enddiv %}After{% enddiv %}End"
        )
        self.assertEqual(
            t.render(c),
            "Start<div id='outer'>Before<div id='inner'>Jack &amp; Jill</div>After"
            "</div>End",
        )
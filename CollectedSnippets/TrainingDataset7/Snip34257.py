def test_different_simple_block_nested(self):
        c = Context({"name": "Jack & Jill"})
        t = self.engine.from_string(
            "{% load custom %}Start{% div id='outer' %}Before"
            "{% simple_keyword_only_default_block %}Inner"
            "{% endsimple_keyword_only_default_block %}"
            "After{% enddiv %}End"
        )
        self.assertEqual(
            t.render(c),
            "Start<div id='outer'>Before"
            "simple_keyword_only_default_block - Expected result (content value: "
            "Inner): 42After</div>End",
        )
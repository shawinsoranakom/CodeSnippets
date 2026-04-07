def test_simple_block_tags(self):
        c = Context({"value": 42})

        templates = [
            (
                "{% load custom %}{% div %}content{% enddiv %}",
                "<div id='test'>content</div>",
            ),
            (
                "{% load custom %}{% one_param_block 37 %}inner"
                "{% endone_param_block %}",
                "one_param_block - Expected result: 37 with content inner",
            ),
            (
                "{% load custom %}{% explicit_no_context_block 37 %}inner"
                "{% endexplicit_no_context_block %}",
                "explicit_no_context_block - Expected result: 37 with content inner",
            ),
            (
                "{% load custom %}{% no_params_with_context_block %}inner"
                "{% endno_params_with_context_block %}",
                "no_params_with_context_block - Expected result (context value: 42) "
                "(content value: inner)",
            ),
            (
                "{% load custom %}{% params_and_context_block 37 %}inner"
                "{% endparams_and_context_block %}",
                "params_and_context_block - Expected result (context value: 42) "
                "(content value: inner): 37",
            ),
            (
                "{% load custom %}{% simple_two_params_block 37 42 %}inner"
                "{% endsimple_two_params_block %}",
                "simple_two_params_block - Expected result (content value: inner): "
                "37, 42",
            ),
            (
                "{% load custom %}{% simple_keyword_only_param_block kwarg=37 %}thirty "
                "seven{% endsimple_keyword_only_param_block %}",
                "simple_keyword_only_param_block - Expected result (content value: "
                "thirty seven): 37",
            ),
            (
                "{% load custom %}{% simple_keyword_only_default_block %}forty two"
                "{% endsimple_keyword_only_default_block %}",
                "simple_keyword_only_default_block - Expected result (content value: "
                "forty two): 42",
            ),
            (
                "{% load custom %}{% simple_keyword_only_default_block kwarg=37 %}"
                "thirty seven{% endsimple_keyword_only_default_block %}",
                "simple_keyword_only_default_block - Expected result (content value: "
                "thirty seven): 37",
            ),
            (
                "{% load custom %}{% simple_one_default_block 37 %}inner"
                "{% endsimple_one_default_block %}",
                "simple_one_default_block - Expected result (content value: inner): "
                "37, hi",
            ),
            (
                '{% load custom %}{% simple_one_default_block 37 two="hello" %}inner'
                "{% endsimple_one_default_block %}",
                "simple_one_default_block - Expected result (content value: inner): "
                "37, hello",
            ),
            (
                '{% load custom %}{% simple_one_default_block one=99 two="hello" %}'
                "inner{% endsimple_one_default_block %}",
                "simple_one_default_block - Expected result (content value: inner): "
                "99, hello",
            ),
            (
                "{% load custom %}{% simple_one_default_block 37 42 %}inner"
                "{% endsimple_one_default_block %}",
                "simple_one_default_block - Expected result (content value: inner): "
                "37, 42",
            ),
            (
                "{% load custom %}{% simple_unlimited_args_block 37 %}thirty seven"
                "{% endsimple_unlimited_args_block %}",
                "simple_unlimited_args_block - Expected result (content value: thirty "
                "seven): 37, hi",
            ),
            (
                "{% load custom %}{% simple_unlimited_args_block 37 42 56 89 %}numbers"
                "{% endsimple_unlimited_args_block %}",
                "simple_unlimited_args_block - Expected result "
                "(content value: numbers): 37, 42, 56, 89",
            ),
            (
                "{% load custom %}{% simple_only_unlimited_args_block %}inner"
                "{% endsimple_only_unlimited_args_block %}",
                "simple_only_unlimited_args_block - Expected result (content value: "
                "inner): ",
            ),
            (
                "{% load custom %}{% simple_only_unlimited_args_block 37 42 56 89 %}"
                "numbers{% endsimple_only_unlimited_args_block %}",
                "simple_only_unlimited_args_block - Expected result "
                "(content value: numbers): 37, 42, 56, 89",
            ),
            (
                "{% load custom %}"
                '{% simple_unlimited_args_kwargs_block 37 40|add:2 56 eggs="scrambled" '
                "four=1|add:3 %}inner content"
                "{% endsimple_unlimited_args_kwargs_block %}",
                "simple_unlimited_args_kwargs_block - Expected result (content value: "
                "inner content): 37, 42, 56 / eggs=scrambled, four=4",
            ),
        ]

        for entry in templates:
            with self.subTest(entry[0]):
                t = self.engine.from_string(entry[0])
                self.assertEqual(t.render(c), entry[1])
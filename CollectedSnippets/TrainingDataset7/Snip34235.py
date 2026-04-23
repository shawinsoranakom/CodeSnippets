def test_simple_tags(self):
        c = Context({"value": 42})

        templates = [
            ("{% load custom %}{% no_params %}", "no_params - Expected result"),
            ("{% load custom %}{% one_param 37 %}", "one_param - Expected result: 37"),
            (
                "{% load custom %}{% explicit_no_context 37 %}",
                "explicit_no_context - Expected result: 37",
            ),
            (
                "{% load custom %}{% no_params_with_context %}",
                "no_params_with_context - Expected result (context value: 42)",
            ),
            (
                "{% load custom %}{% params_and_context 37 %}",
                "params_and_context - Expected result (context value: 42): 37",
            ),
            (
                "{% load custom %}{% simple_two_params 37 42 %}",
                "simple_two_params - Expected result: 37, 42",
            ),
            (
                "{% load custom %}{% simple_keyword_only_param kwarg=37 %}",
                "simple_keyword_only_param - Expected result: 37",
            ),
            (
                "{% load custom %}{% simple_keyword_only_default %}",
                "simple_keyword_only_default - Expected result: 42",
            ),
            (
                "{% load custom %}{% simple_keyword_only_default kwarg=37 %}",
                "simple_keyword_only_default - Expected result: 37",
            ),
            (
                "{% load custom %}{% simple_one_default 37 %}",
                "simple_one_default - Expected result: 37, hi",
            ),
            (
                '{% load custom %}{% simple_one_default 37 two="hello" %}',
                "simple_one_default - Expected result: 37, hello",
            ),
            (
                '{% load custom %}{% simple_one_default one=99 two="hello" %}',
                "simple_one_default - Expected result: 99, hello",
            ),
            (
                "{% load custom %}{% simple_one_default 37 42 %}",
                "simple_one_default - Expected result: 37, 42",
            ),
            (
                "{% load custom %}{% simple_unlimited_args 37 %}",
                "simple_unlimited_args - Expected result: 37, hi",
            ),
            (
                "{% load custom %}{% simple_unlimited_args 37 42 56 89 %}",
                "simple_unlimited_args - Expected result: 37, 42, 56, 89",
            ),
            (
                "{% load custom %}{% simple_only_unlimited_args %}",
                "simple_only_unlimited_args - Expected result: ",
            ),
            (
                "{% load custom %}{% simple_only_unlimited_args 37 42 56 89 %}",
                "simple_only_unlimited_args - Expected result: 37, 42, 56, 89",
            ),
            (
                "{% load custom %}"
                '{% simple_unlimited_args_kwargs 37 40|add:2 56 eggs="scrambled" '
                "four=1|add:3 %}",
                "simple_unlimited_args_kwargs - Expected result: 37, 42, 56 / "
                "eggs=scrambled, four=4",
            ),
        ]

        for entry in templates:
            t = self.engine.from_string(entry[0])
            self.assertEqual(t.render(c), entry[1])

        for entry in templates:
            t = self.engine.from_string(
                "%s as var %%}Result: {{ var }}" % entry[0][0:-2]
            )
            self.assertEqual(t.render(c), "Result: %s" % entry[1])
def test_inclusion_tags(self):
        c = Context({"value": 42})

        templates = [
            (
                "{% load inclusion %}{% inclusion_no_params %}",
                "inclusion_no_params - Expected result\n",
            ),
            (
                "{% load inclusion %}{% inclusion_one_param 37 %}",
                "inclusion_one_param - Expected result: 37\n",
            ),
            (
                "{% load inclusion %}{% inclusion_explicit_no_context 37 %}",
                "inclusion_explicit_no_context - Expected result: 37\n",
            ),
            (
                "{% load inclusion %}{% inclusion_no_params_with_context %}",
                "inclusion_no_params_with_context - Expected result (context value: "
                "42)\n",
            ),
            (
                "{% load inclusion %}{% inclusion_params_and_context 37 %}",
                "inclusion_params_and_context - Expected result (context value: 42): "
                "37\n",
            ),
            (
                "{% load inclusion %}{% inclusion_two_params 37 42 %}",
                "inclusion_two_params - Expected result: 37, 42\n",
            ),
            (
                "{% load inclusion %}{% inclusion_one_default 37 %}",
                "inclusion_one_default - Expected result: 37, hi\n",
            ),
            (
                '{% load inclusion %}{% inclusion_one_default 37 two="hello" %}',
                "inclusion_one_default - Expected result: 37, hello\n",
            ),
            (
                '{% load inclusion %}{% inclusion_one_default one=99 two="hello" %}',
                "inclusion_one_default - Expected result: 99, hello\n",
            ),
            (
                "{% load inclusion %}{% inclusion_one_default 37 42 %}",
                "inclusion_one_default - Expected result: 37, 42\n",
            ),
            (
                "{% load inclusion %}{% inclusion_keyword_only_default kwarg=37 %}",
                "inclusion_keyword_only_default - Expected result: 37\n",
            ),
            (
                "{% load inclusion %}{% inclusion_unlimited_args 37 %}",
                "inclusion_unlimited_args - Expected result: 37, hi\n",
            ),
            (
                "{% load inclusion %}{% inclusion_unlimited_args 37 42 56 89 %}",
                "inclusion_unlimited_args - Expected result: 37, 42, 56, 89\n",
            ),
            (
                "{% load inclusion %}{% inclusion_only_unlimited_args %}",
                "inclusion_only_unlimited_args - Expected result: \n",
            ),
            (
                "{% load inclusion %}{% inclusion_only_unlimited_args 37 42 56 89 %}",
                "inclusion_only_unlimited_args - Expected result: 37, 42, 56, 89\n",
            ),
            (
                "{% load inclusion %}"
                '{% inclusion_unlimited_args_kwargs 37 40|add:2 56 eggs="scrambled" '
                "four=1|add:3 %}",
                "inclusion_unlimited_args_kwargs - Expected result: 37, 42, 56 / "
                "eggs=scrambled, four=4\n",
            ),
        ]

        for entry in templates:
            t = self.engine.from_string(entry[0])
            self.assertEqual(t.render(c), entry[1])
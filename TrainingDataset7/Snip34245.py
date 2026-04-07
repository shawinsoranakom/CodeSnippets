def test_simple_block_tag_errors(self):
        errors = [
            (
                "'simple_one_default_block' received unexpected keyword argument "
                "'three'",
                "{% load custom %}"
                '{% simple_one_default_block 99 two="hello" three="foo" %}'
                "{% endsimple_one_default_block %}",
            ),
            (
                "'simple_two_params_block' received too many positional arguments",
                "{% load custom %}{% simple_two_params_block 37 42 56 %}"
                "{% endsimple_two_params_block %}",
            ),
            (
                "'simple_one_default_block' received too many positional arguments",
                "{% load custom %}{% simple_one_default_block 37 42 56 %}"
                "{% endsimple_one_default_block %}",
            ),
            (
                "'simple_keyword_only_param_block' did not receive value(s) for the "
                "argument(s): 'kwarg'",
                "{% load custom %}{% simple_keyword_only_param_block %}"
                "{% endsimple_keyword_only_param_block %}",
            ),
            (
                "'simple_keyword_only_param_block' received multiple values for "
                "keyword argument 'kwarg'",
                "{% load custom %}"
                "{% simple_keyword_only_param_block kwarg=42 kwarg=37 %}"
                "{% endsimple_keyword_only_param_block %}",
            ),
            (
                "'simple_keyword_only_default_block' received multiple values for "
                "keyword argument 'kwarg'",
                "{% load custom %}{% simple_keyword_only_default_block kwarg=42 "
                "kwarg=37 %}{% endsimple_keyword_only_default_block %}",
            ),
            (
                "'simple_unlimited_args_kwargs_block' received some positional "
                "argument(s) after some keyword argument(s)",
                "{% load custom %}"
                '{% simple_unlimited_args_kwargs_block 37 40|add:2 eggs="scrambled" 56 '
                "four=1|add:3 %}{% endsimple_unlimited_args_kwargs_block %}",
            ),
            (
                "'simple_unlimited_args_kwargs_block' received multiple values for "
                "keyword argument 'eggs'",
                "{% load custom %}"
                "{% simple_unlimited_args_kwargs_block 37 "
                'eggs="scrambled" eggs="scrambled" %}'
                "{% endsimple_unlimited_args_kwargs_block %}",
            ),
            (
                "Unclosed tag on line 1: 'div'. Looking for one of: enddiv.",
                "{% load custom %}{% div %}Some content",
            ),
            (
                "Unclosed tag on line 1: 'simple_one_default_block'. Looking for one "
                "of: endsimple_one_default_block.",
                "{% load custom %}{% simple_one_default_block %}Some content",
            ),
        ]

        for entry in errors:
            with self.subTest(entry[1]):
                with self.assertRaisesMessage(TemplateSyntaxError, entry[0]):
                    self.engine.from_string(entry[1])
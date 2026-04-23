def test_simple_tag_errors(self):
        errors = [
            (
                "'simple_one_default' received unexpected keyword argument 'three'",
                '{% load custom %}{% simple_one_default 99 two="hello" three="foo" %}',
            ),
            (
                "'simple_two_params' received too many positional arguments",
                "{% load custom %}{% simple_two_params 37 42 56 %}",
            ),
            (
                "'simple_one_default' received too many positional arguments",
                "{% load custom %}{% simple_one_default 37 42 56 %}",
            ),
            (
                "'simple_keyword_only_param' did not receive value(s) for the "
                "argument(s): 'kwarg'",
                "{% load custom %}{% simple_keyword_only_param %}",
            ),
            (
                "'simple_keyword_only_param' received multiple values for "
                "keyword argument 'kwarg'",
                "{% load custom %}{% simple_keyword_only_param kwarg=42 kwarg=37 %}",
            ),
            (
                "'simple_keyword_only_default' received multiple values for "
                "keyword argument 'kwarg'",
                "{% load custom %}{% simple_keyword_only_default kwarg=42 "
                "kwarg=37 %}",
            ),
            (
                "'simple_unlimited_args_kwargs' received some positional argument(s) "
                "after some keyword argument(s)",
                "{% load custom %}"
                "{% simple_unlimited_args_kwargs 37 40|add:2 "
                'eggs="scrambled" 56 four=1|add:3 %}',
            ),
            (
                "'simple_unlimited_args_kwargs' received multiple values for keyword "
                "argument 'eggs'",
                "{% load custom %}"
                "{% simple_unlimited_args_kwargs 37 "
                'eggs="scrambled" eggs="scrambled" %}',
            ),
        ]

        for entry in errors:
            with self.assertRaisesMessage(TemplateSyntaxError, entry[0]):
                self.engine.from_string(entry[1])

        for entry in errors:
            with self.assertRaisesMessage(TemplateSyntaxError, entry[0]):
                self.engine.from_string("%s as var %%}" % entry[1][0:-2])
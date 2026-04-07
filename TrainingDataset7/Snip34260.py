def test_inclusion_tag_errors(self):
        errors = [
            (
                "'inclusion_one_default' received unexpected keyword argument 'three'",
                "{% load inclusion %}"
                '{% inclusion_one_default 99 two="hello" three="foo" %}',
            ),
            (
                "'inclusion_two_params' received too many positional arguments",
                "{% load inclusion %}{% inclusion_two_params 37 42 56 %}",
            ),
            (
                "'inclusion_one_default' received too many positional arguments",
                "{% load inclusion %}{% inclusion_one_default 37 42 56 %}",
            ),
            (
                "'inclusion_one_default' did not receive value(s) for the argument(s): "
                "'one'",
                "{% load inclusion %}{% inclusion_one_default %}",
            ),
            (
                "'inclusion_keyword_only_default' received multiple values "
                "for keyword argument 'kwarg'",
                "{% load inclusion %}{% inclusion_keyword_only_default "
                "kwarg=37 kwarg=42 %}",
            ),
            (
                "'inclusion_unlimited_args' did not receive value(s) for the "
                "argument(s): 'one'",
                "{% load inclusion %}{% inclusion_unlimited_args %}",
            ),
            (
                "'inclusion_unlimited_args_kwargs' received some positional "
                "argument(s) after some keyword argument(s)",
                "{% load inclusion %}"
                "{% inclusion_unlimited_args_kwargs 37 40|add:2 "
                'eggs="boiled" 56 four=1|add:3 %}',
            ),
            (
                "'inclusion_unlimited_args_kwargs' received multiple values for "
                "keyword argument 'eggs'",
                "{% load inclusion %}"
                "{% inclusion_unlimited_args_kwargs 37 "
                'eggs="scrambled" eggs="scrambled" %}',
            ),
        ]

        for entry in errors:
            with self.assertRaisesMessage(TemplateSyntaxError, entry[0]):
                self.engine.from_string(entry[1])
def test_include(self):
        """
        #23516 -- This works as a regression test only if the cached loader
        isn't used. Hence we don't use the @setup decorator.
        """
        engine = Engine(
            loaders=[
                (
                    "django.template.loaders.locmem.Loader",
                    {
                        "template": (
                            '{% for x in vars %}{% include "include" %}{% endfor %}'
                        ),
                        "include": "{% ifchanged %}{{ x }}{% endifchanged %}",
                    },
                ),
            ]
        )
        output = engine.render_to_string("template", {"vars": [1, 1, 2, 2, 3, 3]})
        self.assertEqual(output, "123")
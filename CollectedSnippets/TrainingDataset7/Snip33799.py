def test_include_state(self):
        """Tests the node state for different IncludeNodes (#27974)."""
        engine = Engine(
            loaders=[
                (
                    "django.template.loaders.locmem.Loader",
                    {
                        "template": (
                            '{% for x in vars %}{% include "include" %}'
                            '{% include "include" %}{% endfor %}'
                        ),
                        "include": "{% ifchanged %}{{ x }}{% endifchanged %}",
                    },
                ),
            ]
        )
        output = engine.render_to_string("template", {"vars": [1, 1, 2, 2, 3, 3]})
        self.assertEqual(output, "112233")
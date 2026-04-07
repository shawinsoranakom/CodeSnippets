def test_include_cache(self):
        """
        {% include %} keeps resolved templates constant (#27974). The
        CounterNode object in the {% counter %} template tag is created once
        if caching works properly. Each iteration increases the counter instead
        of restarting it.

        This works as a regression test only if the cached loader
        isn't used, so the @setup decorator isn't used.
        """
        engine = Engine(
            loaders=[
                (
                    "django.template.loaders.locmem.Loader",
                    {
                        "template": (
                            '{% for x in vars %}{% include "include" %}{% endfor %}'
                        ),
                        "include": '{% include "next" %}',
                        "next": "{% load custom %}{% counter %}",
                    },
                ),
            ],
            libraries={"custom": "template_tests.templatetags.custom"},
        )
        output = engine.render_to_string("template", {"vars": range(9)})
        self.assertEqual(output, "012345678")
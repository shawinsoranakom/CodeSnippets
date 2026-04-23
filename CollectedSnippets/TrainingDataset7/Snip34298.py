def test_unique_history_per_loader(self):
        """
        Extending should continue even if two loaders return the same
        name for a template.
        """
        engine = Engine(
            loaders=[
                [
                    "django.template.loaders.locmem.Loader",
                    {
                        "base.html": (
                            '{% extends "base.html" %}{% block content %}'
                            "{{ block.super }} loader1{% endblock %}"
                        ),
                    },
                ],
                [
                    "django.template.loaders.locmem.Loader",
                    {
                        "base.html": "{% block content %}loader2{% endblock %}",
                    },
                ],
            ]
        )
        template = engine.get_template("base.html")
        output = template.render(Context({}))
        self.assertEqual(output.strip(), "loader2 loader1")
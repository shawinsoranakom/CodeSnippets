def test_block_override_in_extended_included_template(self):
        """
        ExtendsNode.find_template() initializes history with self.origin
        (#28071).
        """
        engine = Engine(
            loaders=[
                [
                    "django.template.loaders.locmem.Loader",
                    {
                        "base.html": (
                            "{% extends 'base.html' %}{% block base %}{{ block.super }}"
                            "2{% endblock %}"
                        ),
                        "included.html": (
                            "{% extends 'included.html' %}{% block included %}"
                            "{{ block.super }}B{% endblock %}"
                        ),
                    },
                ],
                [
                    "django.template.loaders.locmem.Loader",
                    {
                        "base.html": (
                            "{% block base %}1{% endblock %}"
                            "{% include 'included.html' %}"
                        ),
                        "included.html": "{% block included %}A{% endblock %}",
                    },
                ],
            ],
        )
        template = engine.get_template("base.html")
        self.assertEqual(template.render(Context({})), "12AB")
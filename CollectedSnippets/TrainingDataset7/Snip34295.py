def test_recursive_multiple_loaders(self):
        engine = Engine(
            dirs=[os.path.join(RECURSIVE, "fs")],
            loaders=[
                (
                    "django.template.loaders.locmem.Loader",
                    {
                        "one.html": (
                            '{% extends "one.html" %}{% block content %}'
                            "{{ block.super }} locmem-one{% endblock %}"
                        ),
                        "two.html": (
                            '{% extends "two.html" %}{% block content %}'
                            "{{ block.super }} locmem-two{% endblock %}"
                        ),
                        "three.html": (
                            '{% extends "three.html" %}{% block content %}'
                            "{{ block.super }} locmem-three{% endblock %}"
                        ),
                    },
                ),
                "django.template.loaders.filesystem.Loader",
            ],
        )
        template = engine.get_template("one.html")
        output = template.render(Context({}))
        self.assertEqual(
            output.strip(), "three locmem-three two locmem-two one locmem-one"
        )
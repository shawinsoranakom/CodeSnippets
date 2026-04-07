def test_autoescape_default(self):
        templates = [
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
            }
        ]
        engines = EngineHandler(templates=templates)
        self.assertEqual(
            engines["django"]
            .from_string("Hello, {{ name }}")
            .render({"name": "Bob & Jim"}),
            "Hello, Bob &amp; Jim",
        )
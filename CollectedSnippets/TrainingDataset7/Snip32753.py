def test_autoescape_off(self):
        templates = [
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "OPTIONS": {"autoescape": False},
            }
        ]
        engines = EngineHandler(templates=templates)
        self.assertEqual(
            engines["django"]
            .from_string("Hello, {{ name }}")
            .render({"name": "Bob & Jim"}),
            "Hello, Bob & Jim",
        )
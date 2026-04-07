def test_context_has_priority_over_template_context_processors(self):
        # See ticket #23789.
        engine = DjangoTemplates(
            {
                "DIRS": [],
                "APP_DIRS": False,
                "NAME": "django",
                "OPTIONS": {
                    "context_processors": [test_processor_name],
                },
            }
        )

        template = engine.from_string("{{ processors }}")
        request = self.request_factory.get("/")

        # Context processors run
        content = template.render({}, request)
        self.assertEqual(content, "yes")

        # Context overrides context processors
        content = template.render({"processors": "no"}, request)
        self.assertEqual(content, "no")
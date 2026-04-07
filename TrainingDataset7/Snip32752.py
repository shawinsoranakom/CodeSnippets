def test_builtins_discovery(self):
        engine = DjangoTemplates(
            {
                "DIRS": [],
                "APP_DIRS": False,
                "NAME": "django",
                "OPTIONS": {
                    "builtins": ["template_backends.apps.good.templatetags.good_tags"],
                },
            }
        )

        self.assertEqual(
            engine.engine.builtins,
            [
                "django.template.defaulttags",
                "django.template.defaultfilters",
                "django.template.loader_tags",
                "template_backends.apps.good.templatetags.good_tags",
            ],
        )
def test_templatetag_discovery(self):
        engine = DjangoTemplates(
            {
                "DIRS": [],
                "APP_DIRS": False,
                "NAME": "django",
                "OPTIONS": {
                    "libraries": {
                        "alternate": (
                            "template_backends.apps.good.templatetags.good_tags"
                        ),
                        "override": (
                            "template_backends.apps.good.templatetags.good_tags"
                        ),
                    },
                },
            }
        )

        # libraries are discovered from installed applications
        self.assertEqual(
            engine.engine.libraries["good_tags"],
            "template_backends.apps.good.templatetags.good_tags",
        )
        self.assertEqual(
            engine.engine.libraries["subpackage.tags"],
            "template_backends.apps.good.templatetags.subpackage.tags",
        )
        # libraries are discovered from django.templatetags
        self.assertEqual(
            engine.engine.libraries["static"],
            "django.templatetags.static",
        )
        # libraries passed in OPTIONS are registered
        self.assertEqual(
            engine.engine.libraries["alternate"],
            "template_backends.apps.good.templatetags.good_tags",
        )
        # libraries passed in OPTIONS take precedence over discovered ones
        self.assertEqual(
            engine.engine.libraries["override"],
            "template_backends.apps.good.templatetags.good_tags",
        )
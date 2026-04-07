def test_templatetag_discovery_import_error(self):
        """
        Import errors in tag modules should be reraised with a helpful message.
        """
        with self.assertRaisesMessage(
            InvalidTemplateLibrary,
            "ImportError raised when trying to load "
            "'template_backends.apps.importerror.templatetags.broken_tags'",
        ) as cm:
            DjangoTemplates(
                {
                    "DIRS": [],
                    "APP_DIRS": False,
                    "NAME": "django",
                    "OPTIONS": {},
                }
            )
        self.assertIsInstance(cm.exception.__cause__, ImportError)
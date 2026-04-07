def test_extends_include_missing_cachedloader(self):
        engine = Engine(
            debug=True,
            loaders=[
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.app_directories.Loader",
                    ],
                ),
            ],
        )

        template = engine.get_template("test_extends_error.html")
        with self.assertRaisesMessage(TemplateDoesNotExist, "missing.html"):
            template.render(Context())

        # Repeat to ensure it still works when loading from the cache
        template = engine.get_template("test_extends_error.html")
        with self.assertRaisesMessage(TemplateDoesNotExist, "missing.html"):
            template.render(Context())
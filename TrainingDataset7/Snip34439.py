def test_partials_use_cached_loader_when_configured(self):
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        backend = DjangoTemplates(
            {
                "NAME": "django",
                "DIRS": [template_dir],
                "APP_DIRS": False,
                "OPTIONS": {
                    "loaders": [
                        (
                            "django.template.loaders.cached.Loader",
                            ["django.template.loaders.filesystem.Loader"],
                        ),
                    ],
                },
            }
        )
        cached_loader = backend.engine.template_loaders[0]
        filesystem_loader = cached_loader.loaders[0]

        with mock.patch.object(
            filesystem_loader, "get_contents", wraps=filesystem_loader.get_contents
        ) as mock_get_contents:
            full_template = backend.get_template("partial_examples.html")
            self.assertIn("TEST-PARTIAL-CONTENT", full_template.render({}))

            partial_template = backend.get_template(
                "partial_examples.html#test-partial"
            )
            self.assertEqual(
                "TEST-PARTIAL-CONTENT", partial_template.render({}).strip()
            )

            mock_get_contents.assert_called_once()
def test_context_processor_dependencies_model_backend_subclass(self):
        self.assertEqual(
            admin.checks.check_dependencies(),
            [
                checks.Error(
                    "'django.contrib.auth.context_processors.auth' must be "
                    "enabled in DjangoTemplates (TEMPLATES) if using the default "
                    "auth backend in order to use the admin application.",
                    id="admin.E402",
                ),
            ],
        )
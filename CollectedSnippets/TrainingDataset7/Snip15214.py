def test_no_template_engines(self):
        self.assertEqual(
            admin.checks.check_dependencies(),
            [
                checks.Error(
                    "A 'django.template.backends.django.DjangoTemplates' "
                    "instance must be configured in TEMPLATES in order to use "
                    "the admin application.",
                    id="admin.E403",
                )
            ],
        )
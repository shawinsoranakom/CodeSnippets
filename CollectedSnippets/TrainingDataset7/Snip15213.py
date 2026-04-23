def test_apps_dependencies(self):
        errors = admin.checks.check_dependencies()
        expected = [
            checks.Error(
                "'django.contrib.contenttypes' must be in "
                "INSTALLED_APPS in order to use the admin application.",
                id="admin.E401",
            ),
            checks.Error(
                "'django.contrib.auth' must be in INSTALLED_APPS in order "
                "to use the admin application.",
                id="admin.E405",
            ),
            checks.Error(
                "'django.contrib.messages' must be in INSTALLED_APPS in order "
                "to use the admin application.",
                id="admin.E406",
            ),
        ]
        self.assertEqual(errors, expected)
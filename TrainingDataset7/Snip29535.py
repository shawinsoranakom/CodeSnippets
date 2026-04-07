def assert_model_check_errors(self, model_class, expected_errors):
        errors = model_class.check(databases=self.databases)
        self.assertEqual(errors, [])
        with modify_settings(INSTALLED_APPS={"remove": "django.contrib.postgres"}):
            errors = model_class.check(databases=self.databases)
            self.assertEqual(errors, expected_errors)
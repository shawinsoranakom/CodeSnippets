def test_model_name_max_length(self):
        model_name = "X" * 94
        model = type(model_name, (models.Model,), {"__module__": self.__module__})
        errors = checks.run_checks(self.apps.get_app_configs())
        self.assertEqual(
            errors,
            [
                checks.Error(
                    "The name of model 'auth_tests.%s' must be at most 93 "
                    "characters for its builtin permission codenames to be at "
                    "most 100 characters." % model_name,
                    obj=model,
                    id="auth.E011",
                ),
            ],
        )
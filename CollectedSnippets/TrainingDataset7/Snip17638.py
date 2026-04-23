def test_verbose_name_max_length(self):
        class Checked(models.Model):
            class Meta:
                verbose_name = (
                    "some ridiculously long verbose name that is out of control" * 5
                )

        errors = checks.run_checks(self.apps.get_app_configs())
        self.assertEqual(
            errors,
            [
                checks.Error(
                    "The verbose_name of model 'auth_tests.Checked' must be at most "
                    "244 characters for its builtin permission names to be at most 255 "
                    "characters.",
                    obj=Checked,
                    id="auth.E007",
                ),
            ],
        )
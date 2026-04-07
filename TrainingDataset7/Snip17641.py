def test_custom_permission_codename_max_length(self):
        custom_permission_codename = "x" * 101

        class Checked(models.Model):
            class Meta:
                permissions = [
                    (custom_permission_codename, "Custom permission"),
                ]

        errors = checks.run_checks(self.apps.get_app_configs())
        self.assertEqual(
            errors,
            [
                checks.Error(
                    "The permission codenamed '%s' of model 'auth_tests.Checked' "
                    "is longer than 100 characters." % custom_permission_codename,
                    obj=Checked,
                    id="auth.E012",
                ),
            ],
        )
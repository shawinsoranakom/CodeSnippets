def test_clashing_default_permissions(self):
        class Checked(models.Model):
            class Meta:
                permissions = [("change_checked", "Can edit permission (duplicate)")]

        errors = checks.run_checks(self.apps.get_app_configs())
        self.assertEqual(
            errors,
            [
                checks.Error(
                    "The permission codenamed 'change_checked' clashes with a builtin "
                    "permission for model 'auth_tests.Checked'.",
                    obj=Checked,
                    id="auth.E005",
                ),
            ],
        )
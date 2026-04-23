def test_clashing_custom_permissions(self):
        class Checked(models.Model):
            class Meta:
                permissions = [
                    ("my_custom_permission", "Some permission"),
                    ("other_one", "Some other permission"),
                    (
                        "my_custom_permission",
                        "Some permission with duplicate permission code",
                    ),
                ]

        errors = checks.run_checks(self.apps.get_app_configs())
        self.assertEqual(
            errors,
            [
                checks.Error(
                    "The permission codenamed 'my_custom_permission' is duplicated for "
                    "model 'auth_tests.Checked'.",
                    obj=Checked,
                    id="auth.E006",
                ),
            ],
        )
def test_non_clashing_custom_permissions(self):
        class Checked(models.Model):
            class Meta:
                permissions = [
                    ("my_custom_permission", "Some permission"),
                    ("other_one", "Some other permission"),
                ]

        errors = checks.run_checks(self.apps.get_app_configs())
        self.assertEqual(errors, [])
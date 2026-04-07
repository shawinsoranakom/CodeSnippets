def test_custom_permission_name_max_length(self):
        custom_permission_name = (
            "some ridiculously long verbose name that is out of control" * 5
        )

        class Checked(models.Model):
            class Meta:
                permissions = [
                    ("my_custom_permission", custom_permission_name),
                ]

        errors = checks.run_checks(self.apps.get_app_configs())
        self.assertEqual(
            errors,
            [
                checks.Error(
                    "The permission named '%s' of model 'auth_tests.Checked' is longer "
                    "than 255 characters." % custom_permission_name,
                    obj=Checked,
                    id="auth.E008",
                ),
            ],
        )
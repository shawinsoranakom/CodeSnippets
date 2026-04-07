def test_username_unique_with_model_constraint(self):
        class CustomUserUniqueConstraint(AbstractBaseUser):
            username = models.CharField(max_length=30)
            USERNAME_FIELD = "username"

            class Meta:
                constraints = [
                    UniqueConstraint(fields=["username"], name="username_unique"),
                ]

        self.assertEqual(checks.run_checks(app_configs=self.apps.get_app_configs()), [])
        with self.settings(AUTHENTICATION_BACKENDS=["my.custom.backend"]):
            errors = checks.run_checks(app_configs=self.apps.get_app_configs())
            self.assertEqual(errors, [])
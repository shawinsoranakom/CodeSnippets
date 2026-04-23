def test_required_fields_is_list(self):
        """REQUIRED_FIELDS should be a list."""

        class CustomUserNonListRequiredFields(AbstractBaseUser):
            username = models.CharField(max_length=30, unique=True)
            date_of_birth = models.DateField()

            USERNAME_FIELD = "username"
            REQUIRED_FIELDS = "date_of_birth"

        errors = checks.run_checks(app_configs=self.apps.get_app_configs())
        self.assertEqual(
            errors,
            [
                checks.Error(
                    "'REQUIRED_FIELDS' must be a list or tuple.",
                    obj=CustomUserNonListRequiredFields,
                    id="auth.E001",
                ),
            ],
        )
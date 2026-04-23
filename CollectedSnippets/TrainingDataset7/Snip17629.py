def test_username_not_in_required_fields(self):
        """USERNAME_FIELD should not appear in REQUIRED_FIELDS."""

        class CustomUserBadRequiredFields(AbstractBaseUser):
            username = models.CharField(max_length=30, unique=True)
            date_of_birth = models.DateField()

            USERNAME_FIELD = "username"
            REQUIRED_FIELDS = ["username", "date_of_birth"]

        errors = checks.run_checks(self.apps.get_app_configs())
        self.assertEqual(
            errors,
            [
                checks.Error(
                    "The field named as the 'USERNAME_FIELD' for a custom user model "
                    "must not be included in 'REQUIRED_FIELDS'.",
                    hint=(
                        "The 'USERNAME_FIELD' is currently set to 'username', you "
                        "should remove 'username' from the 'REQUIRED_FIELDS'."
                    ),
                    obj=CustomUserBadRequiredFields,
                    id="auth.E002",
                ),
            ],
        )
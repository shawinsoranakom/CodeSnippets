def test_username_non_unique(self):
        """
        A non-unique USERNAME_FIELD raises an error only if the default
        authentication backend is used. Otherwise, a warning is raised.
        """
        errors = checks.run_checks()
        self.assertEqual(
            errors,
            [
                checks.Error(
                    "'CustomUserNonUniqueUsername.username' must be "
                    "unique because it is named as the 'USERNAME_FIELD'.",
                    obj=CustomUserNonUniqueUsername,
                    id="auth.E003",
                ),
            ],
        )
        with self.settings(AUTHENTICATION_BACKENDS=["my.custom.backend"]):
            errors = checks.run_checks()
            self.assertEqual(
                errors,
                [
                    checks.Warning(
                        "'CustomUserNonUniqueUsername.username' is named as "
                        "the 'USERNAME_FIELD', but it is not unique.",
                        hint=(
                            "Ensure that your authentication backend(s) can handle "
                            "non-unique usernames."
                        ),
                        obj=CustomUserNonUniqueUsername,
                        id="auth.W004",
                    ),
                ],
            )
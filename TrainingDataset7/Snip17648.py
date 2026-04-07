def test_missing_authentication_with_login_required_middleware(self):
        errors = checks.run_checks()
        self.assertEqual(
            errors,
            [
                checks.Error(
                    "In order to use django.contrib.auth.middleware."
                    "LoginRequiredMiddleware, django.contrib.auth.middleware."
                    "AuthenticationMiddleware must be defined before it in MIDDLEWARE.",
                    id="auth.E013",
                )
            ],
        )
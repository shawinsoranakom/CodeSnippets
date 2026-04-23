def test_middleware_dependencies(self):
        errors = admin.checks.check_dependencies()
        expected = [
            checks.Error(
                "'django.contrib.auth.middleware.AuthenticationMiddleware' "
                "must be in MIDDLEWARE in order to use the admin application.",
                id="admin.E408",
            ),
            checks.Error(
                "'django.contrib.messages.middleware.MessageMiddleware' "
                "must be in MIDDLEWARE in order to use the admin application.",
                id="admin.E409",
            ),
            checks.Error(
                "'django.contrib.sessions.middleware.SessionMiddleware' "
                "must be in MIDDLEWARE in order to use the admin application.",
                hint=(
                    "Insert "
                    "'django.contrib.sessions.middleware.SessionMiddleware' "
                    "before "
                    "'django.contrib.auth.middleware.AuthenticationMiddleware'."
                ),
                id="admin.E410",
            ),
        ]
        self.assertEqual(errors, expected)
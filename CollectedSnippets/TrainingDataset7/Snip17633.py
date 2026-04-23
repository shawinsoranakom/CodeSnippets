def test_is_anonymous_authenticated_methods(self):
        """
        <User Model>.is_anonymous/is_authenticated must not be methods.
        """

        class BadUser(AbstractBaseUser):
            username = models.CharField(max_length=30, unique=True)
            USERNAME_FIELD = "username"

            def is_anonymous(self):
                return True

            def is_authenticated(self):
                return True

        errors = checks.run_checks(app_configs=self.apps.get_app_configs())
        self.assertEqual(
            errors,
            [
                checks.Critical(
                    "%s.is_anonymous must be an attribute or property rather than "
                    "a method. Ignoring this is a security issue as anonymous "
                    "users will be treated as authenticated!" % BadUser,
                    obj=BadUser,
                    id="auth.C009",
                ),
                checks.Critical(
                    "%s.is_authenticated must be an attribute or property rather "
                    "than a method. Ignoring this is a security issue as anonymous "
                    "users will be treated as authenticated!" % BadUser,
                    obj=BadUser,
                    id="auth.C010",
                ),
            ],
        )
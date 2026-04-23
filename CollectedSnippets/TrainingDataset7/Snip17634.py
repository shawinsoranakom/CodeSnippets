def test_is_anonymous_authenticated_static_methods(self):
        """
        <User Model>.is_anonymous/is_authenticated must not be static methods.
        """

        class VulnerableStaticUser(AbstractBaseUser):
            username = models.CharField(max_length=30, unique=True)
            USERNAME_FIELD = "username"

            @staticmethod
            def is_anonymous():
                return False

            @staticmethod
            def is_authenticated():
                return False

        errors = checks.run_checks(app_configs=self.apps.get_app_configs())
        self.assertEqual(
            errors,
            [
                checks.Critical(
                    "%s.is_anonymous must be an attribute or property rather than "
                    "a method. Ignoring this is a security issue as anonymous "
                    "users will be treated as authenticated!" % VulnerableStaticUser,
                    obj=VulnerableStaticUser,
                    id="auth.C009",
                ),
                checks.Critical(
                    "%s.is_authenticated must be an attribute or property rather "
                    "than a method. Ignoring this is a security issue as anonymous "
                    "users will be treated as authenticated!" % VulnerableStaticUser,
                    obj=VulnerableStaticUser,
                    id="auth.C010",
                ),
            ],
        )
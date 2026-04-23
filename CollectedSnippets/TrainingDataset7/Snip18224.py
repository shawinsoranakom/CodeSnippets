def test_login_with_custom_user_without_last_login_field(self):
        """
        The user_logged_in signal is only registered if the user model has a
        last_login field.
        """
        last_login_receivers = signals.user_logged_in.receivers
        try:
            signals.user_logged_in.receivers = []
            with self.assertRaises(FieldDoesNotExist):
                MinimalUser._meta.get_field("last_login")
            with self.settings(AUTH_USER_MODEL="auth_tests.MinimalUser"):
                apps.get_app_config("auth").ready()
            self.assertEqual(signals.user_logged_in.receivers, [])

            # last_login is a property whose value is None.
            self.assertIsNone(UserWithDisabledLastLoginField().last_login)
            with self.settings(
                AUTH_USER_MODEL="auth_tests.UserWithDisabledLastLoginField"
            ):
                apps.get_app_config("auth").ready()
            self.assertEqual(signals.user_logged_in.receivers, [])

            with self.settings(AUTH_USER_MODEL="auth.User"):
                apps.get_app_config("auth").ready()
            self.assertEqual(len(signals.user_logged_in.receivers), 1)
        finally:
            signals.user_logged_in.receivers = last_login_receivers
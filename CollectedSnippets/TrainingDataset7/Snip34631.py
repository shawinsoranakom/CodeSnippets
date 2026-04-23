def test_force_login_with_backend_missing_get_user(self):
        """
        force_login() skips auth backends without a get_user() method.
        """
        self.client.force_login(self.u1)
        self.assertEqual(self.u1.backend, "django.contrib.auth.backends.ModelBackend")
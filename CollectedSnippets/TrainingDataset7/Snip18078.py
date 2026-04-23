def test_get_login_url_no_login_url(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            self.middleware.get_login_url(lambda: None)
        self.assertEqual(
            str(e.exception),
            "No login URL to redirect to. Define settings.LOGIN_URL or provide "
            "a login_url via the 'django.contrib.auth.decorators.login_required' "
            "decorator.",
        )
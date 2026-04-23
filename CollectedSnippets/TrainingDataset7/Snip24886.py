def test_invalid_prefix_use(self):
        msg = "Using i18n_patterns in an included URLconf is not allowed."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            reverse("account:register")
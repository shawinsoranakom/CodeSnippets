def test_no_secret_key(self):
        msg = "The SECRET_KEY setting must not be empty."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            settings.SECRET_KEY
def test_secret_lazy_validation(self):
        default_token_generator = PasswordResetTokenGenerator()
        msg = "The SECRET_KEY setting must not be empty."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            default_token_generator.secret
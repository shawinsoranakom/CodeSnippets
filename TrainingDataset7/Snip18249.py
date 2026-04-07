def test_token_with_different_secret_subclass(self):
        class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
            secret = "test-secret"

        user = User.objects.create_user("tokentestuser", "test2@example.com", "testpw")
        custom_password_generator = CustomPasswordResetTokenGenerator()
        tk_custom = custom_password_generator.make_token(user)
        self.assertIs(custom_password_generator.check_token(user, tk_custom), True)

        default_password_generator = PasswordResetTokenGenerator()
        self.assertNotEqual(
            custom_password_generator.secret,
            default_password_generator.secret,
        )
        self.assertEqual(default_password_generator.secret, settings.SECRET_KEY)
        # Tokens created with a different secret don't validate.
        tk_default = default_password_generator.make_token(user)
        self.assertIs(custom_password_generator.check_token(user, tk_default), False)
        self.assertIs(default_password_generator.check_token(user, tk_custom), False)
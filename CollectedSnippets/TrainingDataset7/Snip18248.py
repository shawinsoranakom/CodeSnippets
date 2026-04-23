def test_token_with_different_secret(self):
        """
        A valid token can be created with a secret other than SECRET_KEY by
        using the PasswordResetTokenGenerator.secret attribute.
        """
        user = User.objects.create_user("tokentestuser", "test2@example.com", "testpw")
        new_secret = "abcdefghijkl"
        # Create and check a token with a different secret.
        p0 = PasswordResetTokenGenerator()
        p0.secret = new_secret
        tk0 = p0.make_token(user)
        self.assertIs(p0.check_token(user, tk0), True)
        # Create and check a token with the default secret.
        p1 = PasswordResetTokenGenerator()
        self.assertEqual(p1.secret, settings.SECRET_KEY)
        self.assertNotEqual(p1.secret, new_secret)
        tk1 = p1.make_token(user)
        # Tokens created with a different secret don't validate.
        self.assertIs(p0.check_token(user, tk1), False)
        self.assertIs(p1.check_token(user, tk0), False)
def test_check_token_secret_key_fallbacks_override(self):
        user = User.objects.create_user("tokentestuser", "test2@example.com", "testpw")
        p1 = PasswordResetTokenGenerator()
        p1.secret = "oldsecret"
        tk = p1.make_token(user)
        p2 = PasswordResetTokenGenerator()
        p2.secret_fallbacks = []
        self.assertIs(p2.check_token(user, tk), False)
def test_check_token_secret_key_fallbacks(self):
        user = User.objects.create_user("tokentestuser", "test2@example.com", "testpw")
        p1 = PasswordResetTokenGenerator()
        p1.secret = "oldsecret"
        tk = p1.make_token(user)
        p2 = PasswordResetTokenGenerator()
        self.assertIs(p2.check_token(user, tk), True)
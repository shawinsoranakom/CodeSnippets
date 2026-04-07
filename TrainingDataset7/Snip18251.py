def test_check_token_secret_fallbacks(self):
        user = User.objects.create_user("tokentestuser", "test2@example.com", "testpw")
        p1 = PasswordResetTokenGenerator()
        p1.secret = "secret"
        tk = p1.make_token(user)
        p2 = PasswordResetTokenGenerator()
        p2.secret = "newsecret"
        p2.secret_fallbacks = ["secret"]
        self.assertIs(p1.check_token(user, tk), True)
        self.assertIs(p2.check_token(user, tk), True)